# NCCS calibration module

# Replacing a couple of classes from CLIMADA's calibration module with ones designed for our own modelling pipeline
# The module has the same name as the ones it is replacing, and the classes have the same names with 'NCCS' prepended.

import pandas as pd
import numpy as np
import functools
import copy
import json
import os
import logging
import hashlib
import time
from datetime import timedelta
from collections import namedtuple
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Mapping, Optional, Tuple, Union, Any, Dict, List
from scipy.optimize import Bounds
from numbers import Number
from climada.util.calibrate.base import Output, ConstraintType, OutputEvaluator

from analysis import run_pipeline_from_config
from utils import folder_naming, delete_results


ROUND_DECIMALS = 6   # Number of decimal places to round parameters to when storing them as keys

LOGGER = logging.getLogger(__name__)


@dataclass
class NCCSInput:
    """Define the static input for a calibration task

    Attributes
    ----------
    config : dict
        A config dictionary template to be used as the input to the NCCS modelling 
        pipeline.
    data : pandas.Dataframe
        The observations to compare model outputs to. This is passed to the 
        :py:attr:`cost_func` as the second argument.
    write_impact_functions: Callable
        Method that takes an arbitrary set of arguments and uses them to update the 
        csv files storing impact function data. 
    return_period_impacts_from_config : Callable
        Function that takes a config object, executes the NCCS model pipeline and 
        loads the results back into memory as a pandas.DataFrame that is compatible with the format of
        :py:attr:`data`. The return value of this function will be passed to the 
        :py:attr:`cost_func` as first argument.
    cost_func : Callable
        Function that takes two ``pandas.Dataframe`` objects and returns the scalar
        "cost" between them. The optimization algorithm will try to minimize this
        number. The first argument is the true/correct values (:py:attr:`data`), and the
        second argument is the estimated/predicted values.
    bounds : Mapping (str, {Bounds, tuple(float, float)}), optional
        The bounds for the parameters. Keys: parameter names. Values:
        ``scipy.minimize.Bounds`` instance or tuple of minimum and maximum value.
        Unbounded parameters need not be specified here.
    constraints : Constraint or list of Constraint, optional
        One or multiple instances of ``scipy.minimize.LinearConstraint``,
        ``scipy.minimize.NonlinearConstraint``, or a mapping.
    """

    config: dict
    data: pd.DataFrame
    write_impact_functions: Callable[[str, Path], pd.DataFrame]
    return_period_impacts_from_config: Callable[dict, pd.DataFrame]
    cost_func: Callable[[pd.DataFrame, pd.DataFrame], Number]
    bounds: Optional[Mapping[str, Union[Bounds, Tuple[Number, Number]]]] = None
    constraints: Optional[Union[ConstraintType, list[ConstraintType]]] = None
    linear_param: Optional[str] = None
    save_raw_impacts: bool = False
    save_yearsets: bool = False

    def __post_init__(self):
        LOGGER.debug(f'Creating the NCCSInput object')
        self.nonlinear_params = list(set(self.bounds.keys()).difference({self.linear_param}))



class NCCSOutput(Output):
    # The parent class is just fine
    pass


class NCCSOutputEvaluator(OutputEvaluator):
    # TODO: this isn't compatible with current outputs. But it could wrap some methods that compare the performance simulated impact functions
    pass



@dataclass
class NCCSOptimizer(ABC):
    """Abstract base class (interface) for an optimization

    This defines the interface for optimizers in NCCS. New optimizers can be created
    by deriving from this class and overriding at least the :py:meth:`run` method.

    Attributes
    ----------
    input : Input
        The input object for the optimization task. See :py:class:`Input`.
    """

    input: NCCSInput

    def __post_init__(self):
        # If our objective function is linear in one parameter, we want to cache things
        # TODO make this an a proper in-memory database
        # TODO or should the cache be inside the NCCSBayesianOptimizer where param combinations are registered? It would be a bigger rewrite
        if self.input.linear_param:
            LOGGER.debug('Initialising an NCCSOptimizer with a cache')
            self.cache_enabled = True
            self.cache_keys = sorted(self.input.nonlinear_params)
            self.cache = dict()
        else:
            LOGGER.debug('Initialising an NCCSOptimizer without a cache')
            self.cache_enabled = None
            self.cache_keys = None
            self.cache = None


    def _target_func(self, data: pd.DataFrame, predicted: pd.DataFrame) -> Number:
        """Target function for the optimizer

        The default version of this function simply returns the value of the cost
        function evaluated on the arguments.

        Parameters
        ----------
        data : pandas.DataFrame
            The reference data used for calibration. By default, this is
            :py:attr:`Input.data`.
        predicted : pandas.DataFrame
            The impact predicted by the data calibration after it has been transformed
            into a dataframe by :py:attr:`Input.impact_to_dataframe`.

        Returns
        -------
        The value of the target function for the optimizer.
        """
        return -self.input.cost_func(data, predicted)

    def _kwargs_to_parameter_dict(self, *_, **kwargs) -> Dict[str, Any]:
        """Define how the parameters to :py:meth:`_opt_func` must be transformed

        Optimizers may implement different ways of representing the parameters (e.g.,
        key-value pairs, arrays, etc.). Depending on this representation, the parameters
        must be transformed to match the syntax of the impact function generator used,
        see :py:attr:`Input.impact_func_creator`.

        In this default version, the method simply returns its keyword arguments as
        mapping. Override this method if the optimizer used *does not* represent
        parameters as key-value pairs.

        Parameters
        ----------
        kwargs
            The parameters as key-value pairs.

        Returns
        -------
        The parameters as key-value pairs.
        """
        return kwargs

    def _opt_func(self, *args, **kwargs) -> Number:
        """The optimization function iterated by the optimizer

        This function takes arbitrary arguments from the optimizer, generates a new set
        of impact functions from it, computes the impact, and finally calculates the
        target function value and returns it.

        Parameters
        ----------
        args, kwargs
            Arbitrary arguments from the optimizer, including parameters

        Returns
        -------
        Target function value for the given arguments
        """

        # Create the impact functions from a new parameter estimate and write to file
        params = self._kwargs_to_parameter_dict(*args, **kwargs)
        config = copy.deepcopy(self.input.config)
        config['parameters'] = params


        # 8-digit string to identify the run. (There's a chance we'll get repeated identifiers like this but it's not the end of the world if that happens)
        run_hash = self.hash_params(params)
        config['run_title'] = config['run_title'] + run_hash

        direct_output_dir = folder_naming.get_direct_output_dir(config['run_title'])
        indirect_output_dir = folder_naming.get_indirect_output_dir(config['run_title'])
        results_path = Path(direct_output_dir, 'reproduced_obs.csv')

        # If it's already in the cache but with a different linear variable:
        if self.cache_enabled:
            results = self.read_from_cache(params)
        else:
            results = None

        # If we've run this before
        if results is None and os.path.exists(results_path):
            LOGGER.debug(f'Reading previous model output for this parameter combination: {results_path}')
            # TODO add a check that the parameters in the output file match, just in case we get a hash clash
            results = pd.read_csv(results_path)
            if self.cache:
                self.add_to_cache(params, results)

        # Run the modelling chain
        if results is None:
            LOGGER.debug(f'This run has no previous data saved to disk or cache: we will run the modelling chain. Run title {config["run_title"]}')
            start_time = time.monotonic()

            os.makedirs(direct_output_dir, exist_ok=True)
            os.makedirs(indirect_output_dir, exist_ok=True)

            LOGGER.debug('Writing new impact functions')
            self.input.write_impact_functions(**params)

            LOGGER.debug('Running the pipeline and getting results')
            results = self.input.return_period_impacts_from_config(config)

            LOGGER.debug(f'Saving results to disk: {results_path}')
            results.to_csv(results_path, index=False)
            if self.cache_enabled:
                LOGGER.debug(f'Saving results to cache')
                self.add_to_cache(params, results)

            LOGGER.debug(f'Cleaning up')
            raw_impacts_dir = Path(direct_output_dir, 'impact_raw')
            yearsets_dir = Path(direct_output_dir, 'yearsets')
            if os.path.exists(raw_impacts_dir) and not self.input.save_raw_impacts:
                for f in os.listdir(raw_impacts_dir):
                    os.remove(Path(raw_impacts_dir, f))
            if os.path.exists(yearsets_dir) and not self.input.save_yearsets:
                for f in os.listdir(yearsets_dir):
                    os.remove(Path(yearsets_dir, f))

            end_time = time.monotonic()
            run_time = timedelta(seconds=end_time - start_time)
            LOGGER.info(f'Model pipeline execution took {str(run_time)}')

        # Compute cost function
        return self._target_func(results, self.input.data)


    def add_to_cache(self, params: Mapping[str, Number], results: pd.DataFrame) -> None:
        params_rounded = self._round_param_values(params)
        linear_param_rounded = params_rounded[self.input.linear_param]
        if linear_param_rounded == 0:   # Can't use a zero-value linear param
            return
        key = self._cache_keys_from_params(params_rounded)
        if key in self.cache:
            raise ValueError(f'This already exists in the cache. Why are we writing? Downgrade this to a warning if inevitable sometimes. Params: {params_rounded}')
        self.cache[key] = {linear_param_rounded: results}


    def read_from_cache(self, params: Mapping[str, Number], result_colname: str = 'impact') -> pd.DataFrame:
        params_rounded = self._round_param_values(params)
        linear_param_rounded = params_rounded[self.input.linear_param]
        if linear_param_rounded == 0:   # Can't use a zero-value linear param
            return None

        key = self._cache_keys_from_params(params_rounded)

        if not key in self.cache:
            return None
        results = copy.deepcopy(self.cache[key])
        if len(results) != 1:
            raise ValueError(f'Somehow there are two cached results for params {key}: keys {results.keys()}')

        saved_linear_param = list(results.keys())[0]
        results = results[saved_linear_param]
        if saved_linear_param == 0:
            raise ValueError('We accidentally saved a run where the linear parameter has value 0')

        scaling_factor = params[self.input.linear_param] / saved_linear_param
        if scaling_factor > 10000:
            LOGGER.warning(f'We see a large scaling factor of {scaling_factor} compared to the results. Be careful. Consider setting the bounds for the linear variable > 0')
        results[result_colname] = scaling_factor * results[result_colname]
        LOGGER.debug(f'...results found in cache. Scaling factor: {scaling_factor}')
        return results


    def _cache_keys_from_params(self, params: Mapping[str, Number]):
        if len(self.input.nonlinear_params) == 1:
            return params[self.input.nonlinear_params[0]]
        sorted_keys = sorted(self.input.nonlinear_params)
        return tuple([params[k] for k in sorted_keys])


    @staticmethod
    def _round_param_values(params: Mapping[str, Number]) -> Dict[str, float]:
        return {key: np.round(value, decimals=ROUND_DECIMALS) for key, value in params.items()}
    
    @staticmethod
    def hash_params(params: Mapping[str, Number]) -> str:
        rounded_params = NCCSOptimizer._round_param_values(params)
        rounded_params_str = json.dumps(rounded_params, sort_keys=True)
        return hashlib.sha256(rounded_params_str.encode('utf-8')).hexdigest()[-8:]

    @abstractmethod
    def run(self, **opt_kwargs) -> NCCSOutput:
        """Execute the optimization"""
