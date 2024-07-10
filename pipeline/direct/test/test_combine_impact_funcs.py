import unittest
import numpy as np
from copy import deepcopy

from climada.entity.impact_funcs import ImpactFunc
from pipeline.direct.combine_impact_funcs import ImpactFuncComposable 

class TestImpactFuncComposable(unittest.TestCase):

    def test_compose_works(self):
        impf1 = ImpactFunc.from_sigmoid_impf(
            intensity=(0, 100, 5), L=1.0, k=2., x0=50., haz_type='RF', impf_id=1)
        impf2 = ImpactFunc.from_step_impf(
            intensity=(0, 0.5, 1), haz_type='TC', impf_id=2)
        composed = ImpactFuncComposable.from_impact_funcs([impf1, impf2])
        self.assertEqual(composed.haz_type, impf1.haz_type)
        self.assertEqual(composed.id, impf1.id)
        self.assertEqual(composed.name, impf1.name)
        self.assertTrue(np.all(composed.paa == 1.))
        test_intensity = np.arange(0, 110, 2)
        np.testing.assert_allclose(
            composed.calc_mdr(test_intensity),
            impf2.calc_mdr(impf1.calc_mdr(test_intensity))
        )

    def test_compose_works_with_step(self):
        impf1 = ImpactFunc.from_step_impf(
            intensity=(0, 50, 100), haz_type='TC', impf_id=1)
        impf2 = ImpactFunc.from_sigmoid_impf(
            intensity=(0, 1, 0.05), L=1.0, k=2., x0=0.5, haz_type='RF', impf_id=2)
        composed = ImpactFuncComposable.from_impact_funcs([impf1, impf2])
        test_intensity = np.arange(0, 110, 2)
        np.testing.assert_allclose(
            composed.calc_mdr(test_intensity),
            impf2.calc_mdr(impf1.calc_mdr(test_intensity))
        )
    
    def test_compose_handles_paa(self):
        impf1 = ImpactFunc.from_sigmoid_impf(
            intensity=(0, 100, 5), L=1.0, k=2., x0=50., haz_type='RF', impf_id=1)
        impf1.paa = np.full_like(impf1.paa, 0.5)
        impf2 = ImpactFunc.from_step_impf(
            intensity=(0, 0.5, 1), haz_type='TC', impf_id=2)
        composed = ImpactFuncComposable.from_impact_funcs([impf1, impf2])
        impf1_with_paa1 = deepcopy(impf1)
        impf1_with_paa1.paa = np.ones_like(impf1.paa)
        test_intensity = np.arange(0, 110, 2)
        np.testing.assert_allclose(composed.paa, 0.5)
        np.testing.assert_allclose(
            composed.calc_mdr(test_intensity),
            impf2.calc_mdr(impf1_with_paa1.calc_mdr(test_intensity)) * 0.5
        )
    
    def test_we_can_set_metadata(self):
        impf1 = ImpactFunc.from_sigmoid_impf(
            intensity=(0, 100, 5), L=1.0, k=2., x0=50., haz_type='RF', impf_id=2)
        impf2 = ImpactFunc.from_step_impf(
            intensity=(0, 0.5, 1), haz_type='TC', impf_id=2)
        composed = ImpactFuncComposable.from_impact_funcs([impf1, impf2], id=100, name="test")
        self.assertEqual(composed.id, 100)
        self.assertEqual(composed.name, "test")

    def test_compose_works_with_a_long_chain(self):
        impf1 = ImpactFunc.from_sigmoid_impf(
            intensity=(0, 100, 5), L=1.0, k=2., x0=50., haz_type='RF', impf_id=2)
        impf2 = ImpactFunc.from_sigmoid_impf(
            intensity=(0, 1, 0.05), L=1.0, k=2., x0=0.5, haz_type='BI', impf_id=2)
        impf3, impf4 = impf2, impf2
        composed = ImpactFuncComposable.from_impact_funcs([impf1, impf2, impf3, impf4])
        self.assertEqual(composed.haz_type, impf1.haz_type)
        self.assertEqual(composed.id, impf1.id)
        self.assertEqual(composed.name, impf1.name)
        test_intensity = np.arange(0, 110, 2)
        np.testing.assert_allclose(
            composed.calc_mdr(test_intensity),
            impf4.calc_mdr(impf3.calc_mdr(impf2.calc_mdr(impf1.calc_mdr(test_intensity))))
        )
    
    def test_second_impf_enforces_unit_interval(self):
        pass

    def test_paa_doesnt_affect_composed_mdd(self):
        pass

    def test_compose_works_manually(self):
        pass


class TestImpfInversion(unittest.TestCase):
    def test_inversion_works_on_strictly_increasing(self):
        impf = ImpactFuncComposable(
            intensity=[0, 5, 10, 20],
            mdd=[0., 0.3, 0.8, 1.],
            paa=[1, 1, 1, 1]
            )
        test_intensity = np.arange(0, 20.5, 1)
        np.testing.assert_array_almost_equal(
            test_intensity,
            impf.invert_mdd(impf.calc_mdr(test_intensity))
        )
        test_mdr = np.arange(0, 1.01, 0.05)
        np.testing.assert_array_almost_equal(
            test_mdr,
            impf.calc_mdr(impf.invert_mdd(test_mdr))
        )

    def test_inversion_gives_nan_outside_of_range(self):
        impf = ImpactFuncComposable(
            intensity=[0, 5, 10, 20],
            mdd=[0.2, 0.3, 0.8, 0.9],
            paa=[1, 1, 1, 1]
        )
        test_mdd = [0, 0.3, 0.8, 1]
        target_intensity = [np.nan, 5, 10, np.nan]
        np.testing.assert_array_almost_equal(
            impf.invert_mdd(test_mdd),
            target_intensity
        )

    def test_inversion_works_on_a_step_function(self):
        step = 0.5
        impf = ImpactFuncComposable.from_step_impf((0, step, 1), (0, 1))

        # This is the desired behaviour
        self.assertEqual(impf.invert_mdd(1), 1)
        self.assertEqual(impf.invert_mdd(0), step)