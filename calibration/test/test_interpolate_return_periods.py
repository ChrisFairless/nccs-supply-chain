import sys
import unittest
import numpy as np
import pandas as pd

sys.path.append("../..")
from calibration.interpolate_return_periods import interpolate_return_periods


class TestInterpolateReturnPeriods(unittest.TestCase):

    def test_interpolate_one_country(self):
        example_model = pd.DataFrame({
            'country': ['A', 'A', 'A', 'A'],
            'rp': [4, 3, 2, 1],
            'impact': [30, 20, 10, 0]
        })
        example_obs = pd.DataFrame({
            'country': ['A', 'A', 'A'],
            'rp': [3, 1.5, 1],
            'impact': [100, 50, 50]
        })
        example_output = pd.DataFrame({
            'country': ['A', 'A', 'A'],
            'rp': [3, 1.5, 1],
            'impact': [20, 5, 0]
        }).sort_values(['rp'])

        out = interpolate_return_periods(example_model, example_obs)
        np.testing.assert_allclose(out['rp'], example_output['rp'])
        np.testing.assert_allclose(out['impact'], example_output['impact'])


    def test_interpolate_with_less_data_than_obs_overlapping(self):
        example_model = pd.DataFrame({
            'country': ['A', 'A'],
            'rp': [2, 1],
            'impact': [1, 0]
        })
        example_obs = pd.DataFrame({
            'country': ['A', 'A', 'A'],
            'rp': [3, 1.5, 1],
            'impact': [40, 20, 0]
        })
        example_output = pd.DataFrame({
            'country': ['A', 'A', 'A'],
            'rp': [3, 1.5, 1],
            'impact': [np.nan, 0.5, 0]
        }).sort_values(['rp'])

        out = interpolate_return_periods(example_model, example_obs)
        np.testing.assert_allclose(out['rp'], example_output['rp'])
        np.testing.assert_allclose(out['impact'], example_output['impact'])


    def test_interpolate_with_less_data_than_obs_nonoverlapping(self):
        example_model = pd.DataFrame({
            'country': ['A'],
            'rp': [2],
            'impact': [1]
        })
        example_obs = pd.DataFrame({
            'country': ['A', 'A', 'A'],
            'rp': [3, 1.5, 1],
            'impact': [100, 50, 50]
        })
        example_output = pd.DataFrame({
            'country': ['A', 'A', 'A'],
            'rp': [3, 1.5, 1],
            'impact': [np.nan, np.nan, np.nan]
        }).sort_values(['rp'])

        out = interpolate_return_periods(example_model, example_obs)
        np.testing.assert_allclose(out['rp'], example_output['rp'])
        np.testing.assert_allclose(out['impact'], example_output['impact'])


    def test_interpolate_multiple_countries(self):
        example_model = pd.DataFrame({
            'country': ['A', 'A', 'A', 'A', 'A', 'A', 'B'],
            'rp': [6, 5, 4, 3, 2, 1, 20],
            'impact': [2, 1, 1, 1, 1, 0, 100]
        })
        example_obs = pd.DataFrame({
            'country': ['A', 'A', 'A', 'B'],
            'rp': [3, 1.5, 1, 20],
            'impact': [100, 50, 50, 100]
        })
        example_output = pd.DataFrame({
            'country': ['A', 'A', 'A', 'B'],
            'rp': [3, 1.5, 1, 20],
            'impact': [1, 0.5, 0, 100]
        }).sort_values(['rp'])

        out = interpolate_return_periods(example_model, example_obs)
        np.testing.assert_allclose(out['rp'], example_output['rp'])
        np.testing.assert_allclose(out['impact'], example_output['impact'])


if __name__ == '__main__':
    unittest.main()