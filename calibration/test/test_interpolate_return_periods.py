import sys
import unittest
import numpy as np
import pandas as pd

sys.path.append("../..")
from calibration.interpolate_return_periods import interpolate_return_periods


class TestInterpolateReturnPeriods(unittest.TestCase):

    def test_interpolate_one_country(self):
        example_model = pd.DataFrame({
            'country': ['A', 'A'],
            'rp': [2, 1],
            'impact': [20, 10]
        })
        example_obs = pd.DataFrame({
            'country': ['A', 'A'],
            'rp': [1.5, 1.2],
            'impact': [50, 50]
        })
        example_output = pd.DataFrame({
            'country': ['A', 'A'],
            'rp': [1.5, 1.2],
            'impact': [15, 12]
        }).sort_values(['rp'])

        out = interpolate_return_periods(example_model, example_obs)
        np.testing.assert_allclose(out['rp'], example_output['rp'])
        np.testing.assert_allclose(out['impact'], example_output['impact'])


    def test_interpolate_with_a_single_model_point_with_obs(self):
        example_model = pd.DataFrame({
            'country': ['A'],
            'rp': [1],
            'impact': [10]
        })
        example_obs = pd.DataFrame({
            'country': ['A', 'A'],
            'rp': [2, 1],
            'impact': [200, 100]
        })
        example_output = pd.DataFrame({
            'country': ['A', 'A'],
            'rp': [2, 1],
            'impact': [np.nan, 10]
        }).sort_values(['rp'])

        out = interpolate_return_periods(example_model, example_obs)
        np.testing.assert_allclose(out['rp'], example_output['rp'])
        np.testing.assert_allclose(out['impact'], example_output['impact'])


    def test_interpolate_with_a_single_model_point_without_obs(self):
        example_model = pd.DataFrame({
            'country': ['A'],
            'rp': [1],
            'impact': [10]
        })
        example_obs = pd.DataFrame({
            'country': ['A', 'A'],
            'rp': [2, 0],
            'impact': [20, 0]
        })
        example_output = pd.DataFrame({
            'country': ['A', 'A'],
            'rp': [2, 0],
            'impact': [np.nan, np.nan]
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
            'rp': [3, 2, 0],
            'impact': [40, 20, 0]
        })
        example_output = pd.DataFrame({
            'country': ['A', 'A', 'A'],
            'rp': [3, 2, 0],
            'impact': [np.nan, 1, np.nan]
        }).sort_values(['rp'])

        out = interpolate_return_periods(example_model, example_obs)
        np.testing.assert_allclose(out['rp'], example_output['rp'])
        np.testing.assert_allclose(out['impact'], example_output['impact'])


    def test_interpolate_with_less_data_than_obs_nonoverlapping(self):
        example_model = pd.DataFrame({
            'country': ['A', 'A'],
            'rp': [2, 1],
            'impact': [20, 10]
        })
        example_obs = pd.DataFrame({
            'country': ['A', 'A'],
            'rp': [4, 3],
            'impact': [100, 50]
        })
        example_output = pd.DataFrame({
            'country': ['A', 'A'],
            'rp': [4, 3],
            'impact': [np.nan, np.nan]
        }).sort_values(['rp'])

        out = interpolate_return_periods(example_model, example_obs)
        np.testing.assert_allclose(out['rp'], example_output['rp'])
        np.testing.assert_allclose(out['impact'], example_output['impact'])


    def test_interpolate_multiple_countries(self):
        example_model = pd.DataFrame({
            'country': ['A', 'A', 'B', 'B'],
            'rp': [2, 1, 2, 1],
            'impact': [20, 10, 200, 100]
        })
        example_obs = pd.DataFrame({
            'country': ['A', 'B'],
            'rp': [1.5, 1.5],
            'impact': [1000, 5000]
        })
        example_output = pd.DataFrame({
            'country': ['A', 'B'],
            'rp': [1.5, 1.5],
            'impact': [15, 150]
        }).sort_values(['rp'])

        out = interpolate_return_periods(example_model, example_obs)
        np.testing.assert_allclose(out['rp'], example_output['rp'])
        np.testing.assert_allclose(out['impact'], example_output['impact'])


    def test_interpolate_handles_unreproducible_countries(self):
        example_model = pd.DataFrame({
            'country': ['A', 'A'],
            'rp': [2, 1],
            'impact': [20, 10]
        })
        example_obs = pd.DataFrame({
            'country': ['A', 'B'],
            'rp': [1.5, 2],
            'impact': [1000, 1000]
        })
        example_output = pd.DataFrame({
            'country': ['A', 'B'],
            'rp': [1.5, 2],
            'impact': [15, np.nan]
        })
        out = interpolate_return_periods(example_model, example_obs)
        np.testing.assert_allclose(out['rp'], example_output['rp'])
        np.testing.assert_allclose(out['impact'], example_output['impact'])


if __name__ == '__main__':
    unittest.main()