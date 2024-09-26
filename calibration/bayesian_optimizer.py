# NCCS calibration module

# Replacing a couple of classes from CLIMADA's calibration module with ones designed for our own modelling pipeline
# The module has the same name as the ones it is replacing, and the classes have the same names with 'NCCS' prepended.
import json
import logging
import copy
import os
import numpy as np
import time
from datetime import timedelta
from pathlib import Path
from climada.util.calibrate import BayesianOptimizerOutput, BayesianOptimizer, BayesianOptimizerController
from bayes_opt import BayesianOptimization
from bayes_opt.event import Events
from typing import Mapping
from numbers import Number

from utils.folder_naming import get_output_dir
from dataclasses import dataclass
from calibration.base import NCCSOptimizer, NCCSInput

LOGGER = logging.getLogger(__name__)

class NCCSBayesianOptimizerOutput(BayesianOptimizerOutput):
    pass


class NCCSBayesianOptimizerController(BayesianOptimizerController):
    # Override the from_input method to deal with an input with linear parameters
    # @classmethod
    # def from_input(cls, inp: NCCSInput, sampling_base: float = 4, **kwargs):
    #     """Create a controller from a calibration input

    #     This uses the number of parameters to determine the appropriate values for
    #     :py:attr:`init_points` and :py:attr:`n_iter`. Both values are set to
    #     :math:`b^N`, where :math:`b` is the ``sampling_base`` parameter and :math:`N`
    #     is the number of estimated parameters.

    #     Parameters
    #     ----------
    #     inp : Input
    #         Input to the calibration
    #     sampling_base : float, optional
    #         Base for determining the sample size. Increase this for denser sampling.
    #         Defaults to 4.
    #     kwargs
    #         Keyword argument for the default constructor.
    #     """
    #     num_params = len(inp.bounds)
    #     # If one parameter is linear this reduces the complexity
    #     if inp.linear_param:
    #         num_params -= 1
    #     init_points = round(sampling_base**num_params)
    #     n_iter = round(sampling_base**num_params)
    #     return cls(init_points=init_points, n_iter=n_iter, **kwargs)
    pass

# Here we edit the BayesianOptimization in the BayesianOptimization package itself
# Why? We want to allow the 'probe' method to sample many points at once when 
# we recognise that the cost function is linear in one parameter
class NCCSBayesianOptimization(BayesianOptimization):
    def __init__(self, *args, linear_param: str = None, **kwargs):
        LOGGER.debug('Initialising the NCCSBayesianOptimization')
        self.linear_param = linear_param
        super().__init__(*args, **kwargs)

    def probe(self, params: Mapping[str, Number], lazy: bool=True) -> None:
        """
        Evaluates the function on the given points. Useful to guide the optimizer.

        Parameters
        ----------
        params: dict or list
            The parameters where the optimizer will evaluate the function.

        lazy: bool, optional(default=True)
            If True, the optimizer will evaluate the points when calling
            maximize(). Otherwise it will evaluate it at the moment.
        """
        if not isinstance(params, dict):
            params = self._space.array_to_params(params)  # TODO actually I'd prefer any variable called params to _always_ be a dict, and have this enforced so that we don't mix up keys and values

        if lazy:
            LOGGER.debug(f'Adding params to queue (probe method): {params}')
            self._queue.add(params)
        else:
            if not self.linear_param:
                LOGGER.debug(f'Probing params: {params}')
                self._space.probe(params)
            elif self._how_many_points_at_this_linear_parameter(params) >= 1000:
                # Check we haven't already done this hundreds of times (it happens sometimes if you restart)
                LOGGER.info(f"This parameter combination has been investigated already with over 1000 combinations in the linear parameters. We'll do a normal probe. Look into this if it's unexpected: {params}")
                self._space.probe(params)
            else:
                # If we know our model is linear in one variable, we can run lots of extra probes around our point x for (almost) free
                LOGGER.debug(f'Probing linear param combinations around the linear parameter: {params}')
                x = params[self.linear_param]
                i_key = self.space.keys.index(self.linear_param)
                x_probes = self.add_points_around_value(x, bounds=self.space.bounds[i_key])
                for x in x_probes:
                    new_params = copy.deepcopy(params)
                    new_params.update({self.linear_param: x})
                    self._space.probe(new_params)
            self.dispatch(Events.OPTIMIZATION_STEP)
    
    @staticmethod
    def add_points_around_value(x, bounds) -> np.ndarray:
        scaling = bounds[1] - bounds[0]
        delta = [d**3 for d in np.arange(-1, 1.01, 0.1)]
        x_probes = [x + scaling * d for d in delta]
        x_probes = [x] + [p for p in x_probes if (p >= bounds[0] and p <= bounds[1] and p!= x)]
        return x_probes
    

    def _how_many_points_at_this_linear_parameter(self, params: Mapping[str, Number]) -> int:
        LOGGER.debug(f'Counting the number of points already logged in the target space for the combination of (nonlinear) parameters ({params})')
        if self._space.params.shape[0] == 0:
            LOGGER.debug('... 0 points found (there have not yet been any probes)')
            return 0
        i_non_param = np.where(params.keys() != self.linear_param)
        nonlinear_space_params = self._space.params[i_non_param, ]
        nonlinear_params = copy.deepcopy(params).pop(self.linear_param)
        how_many = (nonlinear_space_params == nonlinear_params).all(axis=1).sum()
        LOGGER.debug(f'... {how_many} points found')
        return how_many


@dataclass
class NCCSBayesianOptimizer(NCCSOptimizer, BayesianOptimizer):
    # Mutliple inheritance here: we want the custom methods we defined in 
    # `NCCSOptimizer`, falling back on the methods defined in CLIMADA's
    # `BayesianOptimizer`
    
    # Fully replaces method in BayesianOptimizer class
    def __post_init__(self, random_state, allow_duplicate_points, bayes_opt_kwds):
        """Create optimizer"""
        LOGGER.debug('Initialising the NCCSBayesianOptimizer')
        NCCSOptimizer.__post_init__(self)

        if bayes_opt_kwds is None:
            bayes_opt_kwds = {}

        if self.input.bounds is None:
            raise ValueError("Input.bounds is required for this optimizer")

        self.optimizer = NCCSBayesianOptimization(
            f=self._opt_func,
            pbounds=self.input.bounds,
            constraint=self.input.constraints,
            random_state=random_state,
            allow_duplicate_points=allow_duplicate_points,
            linear_param=self.input.linear_param,
            **bayes_opt_kwds,
        )

    def run(self, controller: NCCSBayesianOptimizerController) -> NCCSBayesianOptimizerOutput:
        LOGGER.debug('Starting the execution of the NCCSBayesianOptimizer')
        start_time = time.monotonic()
        _ = self.collect_existing_run_data(self.input.config['run_title'])
        output = BayesianOptimizer.run(self, controller)
        end_time = time.monotonic()
        run_time = timedelta(seconds=end_time - start_time)
        LOGGER.info(f'Optimisation complete. Time taken: {str(run_time)}')
        return output

    
    def collect_existing_run_data(self, run_title_root: str) -> None:
        # Looks for previous runs from the same optimisation in the folder defined by the run title
        # We add all the values we find to the Optimizer's probe queue: when it's run these will be read from storage
        job_path_components = run_title_root.split('/')
        job_root = job_path_components[-1]
        output_dir = Path(get_output_dir(), *job_path_components[:-1])
        if os.path.exists(output_dir):
            output_dirs = os.listdir(output_dir)
            LOGGER.info(f'Gathering any data saved from previous runs in {output_dir}')
            existing_run_data = {}
            for di in output_dirs:
                d = Path(output_dir, di)
                job_config_path = Path(d, 'indirect', 'config.json')
                if not os.path.exists(job_config_path):
                    continue
                with open(job_config_path) as f:
                    job_config = json.load(f)
                    params = job_config['parameters']
                    if len(params) != len(self.optimizer._space._keys):
                        LOGGER.info(f'{di}: Uh oh, the model output has a different number of parameters to this config. Have you a different calibration in this folder?. Ignoring this data:')
                        continue
                    if di in existing_run_data.keys():
                        LOGGER.info(f'{di}: We already saw these parameters in a previous folder. Ignoring them: {params}')
                        continue
                    LOGGER.info(f'{di}: Found a folder set up for parameters {params}. Adding to the queue.')
                    self.optimizer.probe(params, lazy=True)
                    existing_run_data[di] = params
        n_previous_runs = len(self.optimizer._queue)
        LOGGER.debug(f'Found a total of {n_previous_runs} existing outputs (full or partial)')
        self.optimizer.init_points = 0 if n_previous_runs >= 5 else 5 - n_previous_runs
        return existing_run_data



class NCCSBayesianOptimizerOutputEvaluator():
    # TODO this doesn't work with the current outputs. If we need it we could adapt it.
    pass
