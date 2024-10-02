import sys
import unittest
import numpy as np
import pandas as pd

sys.path.append("../..")
from calibration.rp_errors import rp_rmse


class TestRPErrors(unittest.TestCase):

    def test_rmse_simple(self):
        example_model = pd.DataFrame({
            'country': ['A', 'A'],
            'rp': [2, 1],
            'impact': [10, 10]
        })
        example_obs = pd.DataFrame({
            'country': ['A', 'A'],
            'rp': [2, 1],
            'impact': [0, 0]
        })

        # Manual calculations for the validation, hashtag showyourworking
        difference = np.array([10, 10])
        squared = np.multiply(difference, difference)
        error = np.sqrt(sum(squared))

        output = rp_rmse(example_model, example_obs)
        self.assertAlmostEqual(output, error)


    def test_rmse_handles_multiple_countries(self):
        example_model = pd.DataFrame({
            'country': ['A', 'A', 'B'],
            'rp': [2, 1, 2],
            'impact': [10, 10, 10]
        })
        example_obs = pd.DataFrame({
            'country': ['A', 'A', 'B'],
            'rp': [2, 1, 1],
            'impact': [0, 0, 0]
        })

        # Manual calculations for the validation, hashtag showyourworking
        difference = np.array([10, 10, 10])
        squared = np.multiply(difference, difference)
        error = np.sqrt(sum(squared))

        output = rp_rmse(example_model, example_obs)
        self.assertAlmostEqual(output, error)


    def test_rmse_interpolates(self):
        example_model = pd.DataFrame({
            'country': ['A', 'A'],
            'rp': [2, 1],
            'impact': [20, 10]
        })
        # Example observations: should match the interpolated model data
        example_obs = pd.DataFrame({
            'country': ['A'],
            'rp': [1.5],
            'impact': [15]
        })
        output = rp_rmse(example_model, example_obs)
        self.assertEqual(output, 0)


    def test_rmse_handles_unreproducible_obs(self):
        example_model = pd.DataFrame({
            'country': ['A', 'A'],
            'rp': [2, 1],
            'impact': [20, 10]
        })
        # Example observations: should match the interpolated model data
        example_obs = pd.DataFrame({
            'country': ['A'],
            'rp': [100, 1.5],
            'impact': [1000, 15]
        })
        
        output = rp_rmse(example_model, example_obs)
        self.assertAlmostEqual(output, 0)


    def test_rmse_handles_unreproducible_countries(self):
        example_model = pd.DataFrame({
            'country': ['A', 'A'],
            'rp': [2, 1],
            'impact': [20, 10]
        })
        # Example observations: should match the interpolated model data
        example_obs = pd.DataFrame({
            'country': ['A', 'B'],
            'rp': [1.5, 2],
            'impact': [15, 1000]
        })
        
        output = rp_rmse(example_model, example_obs)
        self.assertAlmostEqual(output, 0)