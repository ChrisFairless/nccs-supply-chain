# NCCS calibration module

# Replacing a couple of classes from CLIMADA's calibration module with ones designed for our own modelling pipeline
# The module has the same name as the ones it is replacing, and the classes have the same names with 'NCCS' prepended.

import pandas as pd
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Mapping, Optional, Tuple, Union, Any, Dict, List
from scipy.optimize import Bounds
from numbers import Number
from climada.util.calibrate.base import Output, ConstraintType, OutputEvaluator

from analysis import run_pipeline_from_config

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
        return self.input.cost_func(data, predicted)

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
        self.input.config['parameters'] = params
        self.input.write_impact_functions(**params)

        # Run the modelling chain
        results = self.input.return_period_impacts_from_config(self.input.config)

        # Compute cost function
        return self._target_func(results, self.input.data)

    @abstractmethod
    def run(self, **opt_kwargs) -> NCCSOutput:
        """Execute the optimization"""
