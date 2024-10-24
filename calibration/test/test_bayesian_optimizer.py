import sys
sys.path.append("../..")
import unittest
import pandas as pd
import numpy as np
import logging
import pycountry
import os
from pathlib import Path
from calibration.bayesian_optimizer import NCCSBayesianOptimization, NCCSBayesianOptimizerController, NCCSBayesianOptimizer
from calibration.base import NCCSInput, NCCSOptimizer
from nccs.run_configurations.test import test_config
from nccs.utils.folder_naming import get_resources_dir, get_output_dir
from calibration.test.create_test_obs import create_test_obs
from calibration.test.create_test_input import simple_linear_input
from nccs.pipeline.direct.test.create_test_exposures import test_exposures
from calibration.utils import return_period_impacts_from_config, write_sigmoid_impf_to_file
from calibration.rp_errors import rp_rmse
from nccs.utils.delete_results import delete_results_folder


LOGGER = logging.getLogger(__name__)
if not LOGGER.hasHandlers():
    FORMATTER = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    CONSOLE = logging.StreamHandler(stream=sys.stdout)
    CONSOLE.setFormatter(FORMATTER)
    LOGGER.addHandler(CONSOLE)

# TODO
# Test that one probe adds ten points to the calculation
# Test that the cache works when a slightly different parameter set is requested


# Very simple example: our model is a linear fit y = m*(x + c) and our observations give m = 1, c = 0 
def run_linear_calibration(linear_param = None, delete_existing = True):
    test_dir = "unittest_calibration/linear/"

    if delete_existing:
        delete_results_folder(test_dir)

    input = simple_linear_input(test_dir, linear_param)

    # Create and run the optimizer
    opt = NCCSBayesianOptimizer(input)
    controller = NCCSBayesianOptimizerController.from_input(input, min_improvement = 0.1, max_iterations = 2)
    # modify the controller for faster testing
    controller.n_iter = controller.n_iter / 5
    bayes_output = opt.run(controller)
    optimal = bayes_output.get_optimal_params()
    return (bayes_output, optimal)


def run_test_pipeline_calibration(linear_param = None, delete_existing=True):
    test_exposure = test_exposures()
    test_country = test_exposure.gdf['country'][0]
    # test_country = 'Maldives'  # Maldives
    test_dir = "unittest_calibration/pipeline/"

    config_template = {
        "run_title": test_dir + "test_",
        "n_sim_years": 10,                  # Number of stochastic years of supply chain impacts to simulate
        "io_approach": ["ghosh"],           # Supply chain IO to use. One or more of "leontief", "ghosh"
        "force_recalculation": False,       # If an intermediate file or output already exists should it be recalculated?
        "use_s3": False,                    # Also load and save data from an S3 bucket
        "log_level": "INFO",
        "seed": 42,

        # Which parts of the model chain to run:
        "do_direct": True,                  # Calculate direct impacts (that aren't already calculated)
        "do_yearsets": False,                # Calculate direct impact yearsets (that aren't already calculated)
        "do_multihazard": False,            # Also combine hazards to create multi-hazard supply chain shocks
        "do_indirect": False,                # Calculate any indirect supply chain impacts (that aren't already calculated)

        # Impact functions:
        "business_interruption": False,      # Turn off to assume % asset loss = % production loss. Mostly for debugging and reproducibility
        "calibrated": "custom",              # True: best calibration. False: best guesstimate impact functions.
                                             # Any other value: looks for custom.csv in the relevant resources/impact_functions/ directory, and falls back on True
        # Parallisation:
        "do_parallel": False,                # Parallelise some operations
        "ncpus": 1,

        # Run specifications:
        "runs": [
            {
                # "hazard": "test",
                # "sectors": ["test"],
                "hazard": "tropical_cyclone",
                "sectors": ["economic_assets"],
                "countries": [test_country],
                "scenario_years": [
                    {"scenario": "None", "ref_year": "historical"},
                ]
            },
        ]
    }

    if delete_existing:
        delete_results_folder(test_dir)
    
    bounds = {'v_half': [0.01, 1], 'scale': [0.01, 1]}
    constraints = None
    test_data = create_test_obs()
    write_impact_functions = lambda v_half, scale: write_sigmoid_impf_to_file('test', v_half, scale, v_thresh=0)

    input = NCCSInput(
        config = config_template,
        data = test_data,
        write_impact_functions = write_impact_functions,
        return_period_impacts_from_config = return_period_impacts_from_config,
        cost_func = rp_rmse,
        bounds = bounds,
        constraints = constraints,
        linear_param=linear_param
    )

    # Create and run the optimizer
    opt = NCCSBayesianOptimizer(input)
    controller = NCCSBayesianOptimizerController.from_input(input, min_improvement = 0.01, max_iterations = 2)
    # modify the controller for faster testing
    controller.n_iter = np.ceil(controller.n_iter / 2) 
    bayes_output = opt.run(controller)
    optimal = bayes_output.get_optimal_params()
    return (bayes_output, optimal)


class TestNCCSBayesianOptimization(unittest.TestCase):
    pass

class TestNCCSBayesianOptimizerController(unittest.TestCase):
    pass

class TestNCCSInput(unittest.TestCase):
    pass

class TestNCCSOptimizer(unittest.TestCase):

    def test_the_calibration_runs(self):
        output, optimal = run_linear_calibration(linear_param = None)
        self.assertTrue(abs(optimal['m'] - 1) < 0.01)     
        self.assertTrue(optimal['c'] < 0.01) 
        n_iters = output.p_space_to_dataframe().shape[0]
        output_folders = [d for d in os.listdir(Path(get_output_dir(), "unittest_calibration/linear/")) if d[0:4] == 'test']
        self.assertEqual(n_iters, len(output_folders))
        for d in output_folders:
            output_location = Path(get_output_dir(), "unittest_calibration/linear/", d, 'direct', 'reproduced_obs.csv')
            self.assertTrue(os.path.exists(output_location))


    def test_we_can_set_linear_params(self):
        output, optimal = run_linear_calibration(linear_param = 'm')
        self.assertTrue(abs(optimal['m'] - 1) < 0.01)     
        self.assertTrue(optimal['c'] < 0.01)     
        n_iters = output.p_space_to_dataframe().shape[0]
        output_folders = [d for d in os.listdir(Path(get_output_dir(), "unittest_calibration/linear/")) if d[0:4] == 'test']
        self.assertTrue(n_iters > 2 * len(output_folders))
        for d in output_folders:
            output_location = Path(get_output_dir(), "unittest_calibration/linear/", d, 'direct', 'reproduced_obs.csv')
            self.assertTrue(os.path.exists(output_location))


    def test_we_can_run_twice_in_the_same_folder_nonlinear(self):
        output1, optimal1 = run_linear_calibration(linear_param = None)
        n_output_runs1 = output1.p_space_to_dataframe().shape[0]
        output2, optimal2 = run_linear_calibration(linear_param = None, delete_existing=False)
        n_output_runs2 = output2.p_space_to_dataframe().shape[0]
        self.assertTrue(abs(optimal2['m'] - 1) < 0.01)     
        self.assertTrue(optimal2['c'] < 0.01)
        self.assertEqual(n_output_runs1, n_output_runs2)


    def test_we_can_run_twice_in_the_same_folder_linear(self):
        output1, optimal1 = run_linear_calibration(linear_param = 'm')
        n_output_runs1 = output1.p_space_to_dataframe().shape[0]
        output2, optimal2 = run_linear_calibration(linear_param = 'm', delete_existing=False)
        n_output_runs2 = output2.p_space_to_dataframe().shape[0]
        self.assertTrue(abs(optimal2['m'] - 1) < 0.01)     
        self.assertTrue(optimal2['c'] < 0.01)
        self.assertEqual(n_output_runs1, n_output_runs2)


    def test_we_can_calibrate_linear_params(self):
        # output1, optimal1 = run_linear_calibration(linear_param=None, delete_existing=True)
        # output2, optimal2 = run_linear_calibration(linear_param='m', delete_existing=True)
        output1, optimal1 = run_test_pipeline_calibration(linear_param=None, delete_existing=True)
        output2, optimal2 = run_test_pipeline_calibration(linear_param='scale', delete_existing=True)
        optimal_cost1 = output1.p_space_to_dataframe()[('Calibration', 'Cost Function')].min()
        optimal_cost2 = output2.p_space_to_dataframe()[('Calibration', 'Cost Function')].min()
        self.assertTrue(abs(optimal_cost1 - optimal_cost2) / optimal_cost1 < 0.01)
        for v1, v2 in zip(optimal1.values(), optimal2.values()):
            self.assertTrue(abs(v1 - v2) < 0.01)

    # def test_the_calibration_is_roughly_reproducible(self):
    #     output1, optimal1 = run_test_pipeline_calibration(linear_param='scale', delete_existing=True)
    #     output2, optimal2 = run_test_pipeline_calibration(linear_param='scale', delete_existing=True)
    #     print('C2 optimal values 1')
    #     print(optimal1)
    #     print('C2 optimal values 2')
    #     print(optimal2)
    #     for v1, v2 in zip(optimal1.values(), optimal2.values()):
    #         self.assertTrue(abs((v1 - v2) / v2) < 0.01)

    def test_the_calibration_behaves_when_run_twice_in_the_same_folder(self):
        output1, optimal1 = run_linear_calibration(linear_param='m', delete_existing=True)
        output2, optimal2 = run_linear_calibration(linear_param='m', delete_existing=False)
        for v1, v2 in zip(optimal1.values(), optimal2.values()):
            self.assertTrue(abs(v1 - v2) < 0.01)
        self.assertTrue(abs(output1.p_space.params.shape[0] - output2.p_space.params.shape[0]) / output2.p_space.params.shape[0] < 0.1)

    
    def test_the_realistic_calibration_behaves_when_run_twice_in_the_same_folder(self):
        output1, optimal1 = run_test_pipeline_calibration(linear_param='scale', delete_existing=True)
        output2, optimal2 = run_test_pipeline_calibration(linear_param='scale', delete_existing=False)
        print(optimal1)
        print(optimal2)
        for v1, v2 in zip(optimal1.values(), optimal2.values()):
            self.assertTrue(abs(v1 - v2) < 0.01)
        print(output1.p_space.params.shape[0])
        print(output2.p_space.params.shape[0])
        self.assertTrue(abs(output1.p_space.params.shape[0] - output2.p_space.params.shape[0]) / output2.p_space.params.shape[0] < 0.1)


    def we_can_swap_the_order_of_inputs(self):
        # while one var is linear
        pass


    def we_can_handle_countries_with_no_impact(self):
        pass


if __name__ == "__main__":
    unittest.main()