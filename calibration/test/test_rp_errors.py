import sys
import unittest
import numpy as np
import pandas as pd

sys.path.append("../..")
from calibration.rp_errors import rp_rmse


class TestInterpolateReturnPeriods(unittest.TestCase):

    def test_rmse(self):
        example_model = pd.DataFrame({
            'country': ['A', 'A', 'A', 'A', 'B'],
            'rp': [4, 3, 2, 1, 4],
            'impact': [30, 20, 10, 0, 30]
        })
        example_obs = pd.DataFrame({
            'country': ['A', 'A', 'A', 'B'],
            'rp': [3, 1.5, 1, 3],
            'impact': [30, 15, 0, 20]
        })

        # Manual calculations for the validation, hashtag showyourworking
        interpolated = pd.DataFrame({
            'country': ['A', 'A', 'A', 'B'],
            'rp': [3, 1.5, 1, 4],
            'impact': [20, 5, 0, 30]
        }).sort_values(['rp'])
        
        difference = np.array([10, 10, 0, -10])
        squared = np.multiply(difference, difference)
        error = np.sqrt(sum(squared))

        output = rp_rmse(example_model, example_obs)
        self.assertAlmostEqual(output, error)