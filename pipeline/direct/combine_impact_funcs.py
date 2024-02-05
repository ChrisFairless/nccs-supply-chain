import numpy as np
from typing import Union, List
from climada.entity import ImpactFunc, ImpfTropCyclone
from climada.entity.impact_funcs.storm_europe import ImpfStormEurope
from climada_petals.entity.impact_funcs.wildfire import ImpfWildfire


class ComposeImpfMixin:
    """
    Extension of the CLIMADA ImpactFunc class allowing for an impact to be 
    modified or adjusted by a second impact function.

    This is useful when trying to keep a modelled damage and the damage used 
    for a calculation conceptually separate (or when uncertainties in their 
    parameters need to be modelled separately).

    e.g. Scaling losses by region to account for known biases
    e.g. Converting asset damage to business interruption
    """

    def compose(
            self,
            impf2: ImpactFunc,
            id: Union[str, int] = None,
            name: str = ""
        ):
        """
        Modifies the impact function by applying a second impact function which 
        takes fractional asset loss as intensity and returns fractional asset loss.

        Mathematically this is a convolution of the two impact functions, i.e.
        impf2(impf1(haz)).

        Parameters
        ----------
        impf2: climada.entity.ImpactFunc
            An impact function with intensity values in the range [0, 1]
        id: str or int, optional
            An ID to use in the resulting function. If not supplied, the id of 
            this function is used
        name: str
            A name for the resulting impact function

        Return
        ------
        impf: ImpactFuncNCCS
            An impact function with updated values of MDD. PAA is unaffected.

        """
        if min(impf2.intensity) < 0 or max(impf2.intensity) > 1:
            raise ValueError('impf_bi should have intensity values in the range [0, 1]')
        if not all(impf2.paa == 1):
            raise ValueError('impf_bi should have paa constant and equal to 1')

        mdd = impf2.calc_mdr(self.calc_mdr(self.intensity))

        return ImpactFuncNCCS(
            haz_type = self.haz_type,
            id = id if id else self.id,
            intensity = self.intensity,
            mdd = impf2.calc_mdr(self.intensity),
            paa = self.paa,
            intensity_unit = self.intensity_unit,
            name = name            
        )


    @classmethod
    def from_impf(cls, impf):
        return cls(*impf.__dict__)

    @classmethod
    def from_combined_impfs(
        cls,
        impf_haz: ImpactFunc,
        impf_bi: ImpactFunc,
        id: Union[str, int] = None,
        name: str = ""
        ):
        impf_haz = cls.from_impf(impf_haz)
        return impf_haz.compose(impf_bi, id, name)
    

class ImpactFuncComposable(ComposeImpfMixin, ImpactFunc):
    pass

class ImpfTropCycloneComposable(ComposeImpfMixin, ImpfTropCyclone):
    pass

class ImpfWildfireComposable(ComposeImpfMixin, ImpfWildfire):
    pass

class ImpfStormEuropeComposable(ComposeImpfMixin, ImpfStormEurope):
    pass
