import sys
sys.path.append("../..")

import os
import unittest
import pandas as pd
from unittest.mock import patch
from pathlib import Path
from copy import deepcopy
from calibration.base import NCCSOptimizer
from calibration.test.create_test_input import simple_linear_input
from calibration.test.create_test_obs import create_test_obs
from utils import folder_naming
from utils.delete_results import delete_results_folder


test_dir = 'unittest_calibration/base/'



class TestNCCSOptimizer(unittest.TestCase):

    def test_hashing_works(self):
        params = {'scale': 0.9173697994106011, 'v_half': 103.22509278018399}
        param_hash = NCCSOptimizer.hash_params(params)
        target = 'd9e9d9dd' # cute name
        self.assertEqual(param_hash, target)

    def test_hashing_allows_for_small_changes(self):
        params1 = {'scale': 0.9173697994106011, 'v_half': 103.22509278018399}
        params2 = {'scale': 0.9173697999999999, 'v_half': 103.22509278099999}
        param1_hash = NCCSOptimizer.hash_params(params1)
        param2_hash = NCCSOptimizer.hash_params(params2)
        self.assertEqual(param1_hash, param2_hash)

    @patch.multiple(NCCSOptimizer, __abstractmethods__=set())
    def test__target_fun_is_zero_for_match(self):
        test_input = simple_linear_input(test_dir)
        opt = NCCSOptimizer(input=test_input)
        test_obs = create_test_obs()
        perfect_match = deepcopy(test_obs)
        diff = opt._target_func(test_obs, perfect_match)
        self.assertEqual(diff, 0)

    @patch.multiple(NCCSOptimizer, __abstractmethods__=set())
    def test__target_fun_gets_worse_with_worse_fit(self):
        test_input = simple_linear_input(test_dir)
        opt = NCCSOptimizer(input=test_input)
        test_obs = pd.DataFrame({
            'country': ['test', 'test'],
            'rp': [2, 1],
            'impact': [1, 0]
        })

        previous_cost = 0
        for i in range(2, 4):
            dummy_model = deepcopy(test_obs)
            dummy_model['impact'] = i * dummy_model['impact']
            cost = opt._target_func(test_obs, dummy_model)
            self.assertTrue(cost <= 0)
            self.assertTrue(cost < previous_cost)
            previous_cost = cost
        

    @patch.multiple(NCCSOptimizer, __abstractmethods__=set())
    def test__opt_fun_runs_with_input_dict(self):
        delete_results_folder(test_dir)
        test_params = {'m': 1.0, 'c': 0.0}
        test_input = simple_linear_input(test_dir, linear_param=None)
        opt = NCCSOptimizer(input=test_input)
        run_hash = NCCSOptimizer.hash_params(test_params)
        cost = opt._opt_func(**test_params)
        direct_output_dir = folder_naming.get_direct_output_dir(test_input.config['run_title'] + run_hash)
        output_obs_path = Path(direct_output_dir, 'reproduced_obs.csv')
        self.assertFalse(opt.cache_enabled)
        self.assertTrue(os.path.exists(output_obs_path))
        self.assertTrue(cost < 0.01)


    # @patch.multiple(NCCSOptimizer, __abstractmethods__=set())
    # def test__opt_fun_runs_with_input_list(self):
    #     delete_results_folder(test_dir)
    #     test_params = [1, 0]
    #     test_input = simple_linear_input(test_dir, linear_param=None)
    #     opt = NCCSOptimizer(input=test_input)
    #     cost = opt._opt_func(*test_params)
    #     self.assertTrue(os.path.exists(output_obs_path))
    #     self.assertTrue(cost < 0.01)


    @patch.multiple(NCCSOptimizer, __abstractmethods__=set())
    def test__opt_fun_reads_existing_output(self):
        delete_results_folder(test_dir)
        test_params = {'m': 1.0, 'c': 0.0}
        run_hash = NCCSOptimizer.hash_params(test_params)
        test_input = simple_linear_input(test_dir)
        opt = NCCSOptimizer(input=test_input)
        cost1 = opt._opt_func(**test_params)
        
        # Now edit the saved output before running something that will read it back in
        direct_output_dir = folder_naming.get_direct_output_dir(test_input.config['run_title'] + run_hash)
        output_obs_path = Path(direct_output_dir, 'reproduced_obs.csv')
        fake_obs = pd.read_csv(output_obs_path)
        fake_obs['impact'] = 0
        fake_obs.to_csv(output_obs_path)

        opt = NCCSOptimizer(input=test_input)
        cost2 = opt._opt_func(**test_params)
        self.assertFalse(cost1 == cost2)


    @patch.multiple(NCCSOptimizer, __abstractmethods__=set())
    def test__opt_fun_handles_linear_param(self):
        delete_results_folder(test_dir)
        test_params = {'m': 1.0, 'c': 0.0}
        test_input = simple_linear_input(test_dir, linear_param='m')
        opt = NCCSOptimizer(input=test_input)
        cost = opt._opt_func(**test_params)
        self.assertTrue(cost < 0.01)

    
    @patch.multiple(NCCSOptimizer, __abstractmethods__=set())
    def test__opt_fun_reads_from_cache(self):
        delete_results_folder(test_dir)
        test_params = {'m': 1.0, 'c': 1.0}
        test_input = simple_linear_input(test_dir, linear_param='m')
        opt = NCCSOptimizer(input=test_input)
        cost1 = opt._opt_func(**test_params)
        self.assertEqual(len(opt.cache), 1)
        self.assertEqual(list(opt.cache.keys()), [1.0])
        self.assertEqual(list(opt.cache[1.0].keys()), [1.0])

        # Edit the saved output to check it's read back in
        key1 = list(opt.cache.keys())[0]
        key2 = list(opt.cache[key1].keys())[0]
        fake_obs = opt.cache[key1][key2]
        fake_obs['impact'] = 0
        opt.cache[key1][key2] = fake_obs
        cost2 = opt._opt_func(**test_params)
        self.assertTrue(cost2 != cost1)


    @patch.multiple(NCCSOptimizer, __abstractmethods__=set())
    def test__opt_fun_reads_from_cache_with_different_linear_values(self):
        delete_results_folder(test_dir)
        test_params = {'m': 1.0, 'c': 1.0}
        test_input = simple_linear_input(test_dir, linear_param='m')
        test_input.data['impact'] = 0  # Set target losses to zero so we can better check changes to modelled results
        opt = NCCSOptimizer(input=test_input)
        cost1 = opt._opt_func(**test_params)
        self.assertEqual(len(opt.cache), 1)

        # If we halve the value of the linear variable that indexes the cached observation, it should double the cost function when it's recalled
        key1 = list(opt.cache.keys())[0]
        key2 = list(opt.cache[key1].keys())[0]
        model_obs = opt.cache[key1].pop(key2)
        opt.cache[key1][0.5] = model_obs
        cost2 = opt._opt_func(**test_params)
        self.assertEqual(cost1 * 2, cost2)


    @patch.multiple(NCCSOptimizer, __abstractmethods__=set())
    def test__opt_fun_generates_consistent_hashes(self):
        delete_results_folder(test_dir)
        test_params = {'m': 1.0, 'c': 0.0}
        test_input = simple_linear_input(test_dir, linear_param='m')
        opt = NCCSOptimizer(input=test_input)
        cost = opt._opt_func(**test_params)
        run_hash = NCCSOptimizer.hash_params(test_params)
        run_dir = Path(folder_naming.get_output_dir(), opt.input.config['run_title'] + run_hash)
        self.assertTrue(os.path.exists(run_dir))


    @patch.multiple(NCCSOptimizer, __abstractmethods__=set())
    def test__opt_fun_works_with_3_parameters(self):
        pass


