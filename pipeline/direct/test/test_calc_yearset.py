import unittest
import numpy as np
from copy import deepcopy
from scipy import sparse

from pipeline.direct.calc_yearset import nccs_yearsets_simple
from pipeline.direct.test.create_test_impact import dummy_impact, dummy_impact_yearly

seed = 1312
np.random.seed(seed)

class TestYearsets(unittest.TestCase):

    def setUp(self):
        self.n_sim_years = 10
        self.dummy_imp = dummy_impact()
        self.dummy_imp_yearly = dummy_impact_yearly()
        self.dummy_imp_yearly.frequency = np.ones_like(self.dummy_imp_yearly.frequency)

    def test_yearset_with_poisson_process(self):
        """Yearsets have their basic functionality working"""
        yimp = nccs_yearsets_simple([self.dummy_imp], n_sim_years = self.n_sim_years, seed=seed)
        np.testing.assert_array_almost_equal(self.dummy_imp.imp_mat.shape, (6, 2))
        np.testing.assert_array_almost_equal(yimp[0].imp_mat.shape, (self.n_sim_years, 2))
        # The max yearset impact is greater than any individual event (with this seed)
        self.assertTrue(np.max(self.dummy_imp.at_event) < np.max(yimp[0].at_event))

    def test_yearset_with_non_poisson_process(self):
        """Our implementation of yearsets can handle sampling event sets where we always want exactly one event per year"""
        yimp = nccs_yearsets_simple([self.dummy_imp_yearly], n_sim_years = self.n_sim_years, seed=seed)
        np.testing.assert_array_almost_equal(self.dummy_imp_yearly.imp_mat.shape, (6, 2))
        np.testing.assert_array_almost_equal(yimp[0].imp_mat.shape, (self.n_sim_years, 2))
        # The max yearset impact is the same as the source impact (with this seed)
        self.assertTrue(np.max(self.dummy_imp_yearly.at_event) == np.max(yimp[0].at_event))

    def test_yearsets_sample_consistently_across_impacts(self):
        """Yearsets use the same sampling method for each impact object they're given"""
        yimp1 = nccs_yearsets_simple([self.dummy_imp, self.dummy_imp], n_sim_years = self.n_sim_years, seed=seed)
        yimp2 = nccs_yearsets_simple([self.dummy_imp_yearly, self.dummy_imp_yearly], n_sim_years = self.n_sim_years, seed=seed)
        np.testing.assert_allclose(yimp1[0].at_event, yimp1[1].at_event)
        np.testing.assert_allclose(yimp2[0].at_event, yimp2[1].at_event)

    def test_yearsets_sample_consistently_when_repeated(self):
        """If we generate yearsets a second time with the same seed we get the same sampling"""
        yimp1 = nccs_yearsets_simple([self.dummy_imp], n_sim_years = self.n_sim_years, seed=seed)
        yimp2 = nccs_yearsets_simple([self.dummy_imp], n_sim_years = self.n_sim_years, seed=seed)
        yimp3 = nccs_yearsets_simple([self.dummy_imp, self.dummy_imp], n_sim_years = self.n_sim_years, seed=seed)
        np.testing.assert_allclose(yimp1[0].at_event, yimp2[0].at_event)
        np.testing.assert_allclose(yimp1[0].at_event, yimp3[0].at_event)
        np.testing.assert_allclose(yimp1[0].at_event, yimp3[1].at_event)

    def test_yearsets_sample_differently_without_a_seed(self):
        """...but if we don't set the seed we get a different sampling"""
        yimp1 = nccs_yearsets_simple([self.dummy_imp], n_sim_years = self.n_sim_years, seed=seed)
        yimp2 = nccs_yearsets_simple([self.dummy_imp], n_sim_years = self.n_sim_years)
        self.assertFalse(np.all(yimp1[0].at_event == yimp2[0].at_event))


if __name__ == '__main__':
    unittest.main()