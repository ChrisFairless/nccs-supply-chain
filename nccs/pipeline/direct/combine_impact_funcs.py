import numpy as np
import pandas as pd
from typing import Union, List
from climada.entity import ImpactFunc


class ImpactFuncComposable(ImpactFunc):
    """
    Extension of the CLIMADA ImpactFunc class allowing for an impact to be 
    modified or adjusted by a second impact function.

    This is useful when trying to keep a modelled damage and the damage used 
    for a calculation conceptually separate (or when uncertainties in their 
    parameters need to be modelled separately).

    e.g. Scaling losses by region to account for known biases
    e.g. Converting asset damage to business interruption
    """

    @classmethod
    def from_impact_funcs(
            cls,
            impf_list: List[ImpactFunc],
            id: Union[str, int] = None,
            name: str = "",
            enforce_unit_interval_impacts = True
        ):
        """
        Composes a list of impact functions into a single impact function. The first 
        function on the list can be any impact function that relates a hazard 
        intensity to a fractional impact. All subseequent functions should take 
        fractional asset loss as 'intensity' and return fractional asset loss.

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
        out = cls.from_impf(impf_list[0])
        for impf in impf_list[1:]:
            out = out.compose(impf, id, name, enforce_unit_interval_impacts)
        return out

    @classmethod
    def from_impf(cls, impf):
        # Ensure intensity and mdd are monotonically increasing (required for invert_mdd later)
        assert(is_monotonic(impf.intensity, only_increasing = True))
        assert(is_monotonic(impf.mdd, only_increasing = True))
        return cls(
            haz_type = impf.haz_type,
            id = impf.id,
            intensity = impf.intensity,
            mdd = impf.mdd,
            paa = impf.paa,
            intensity_unit = impf.intensity_unit,
            name = impf.name
        )
    
    def compose(
            self,    
            impf: ImpactFunc,
            id: Union[str, int] = None,
            name: str = "",
            enforce_unit_interval_impacts = True
        ):

        if min(impf.intensity) < 0:
            raise ValueError('When composing, the second impf should have intensity values >= 0')
        if enforce_unit_interval_impacts and max(impf.intensity) > 1:
            raise ValueError("""When composing, the second impf should have intensity values <= 1.
                             If you want to override this, set enforce_unit_interval_impacts = False""")
        if not np.all(np.array(impf.paa) == 1):
            raise ValueError('When composing, the second impf must have paa constant and equal to 1')


        mapped_nodes_from_self = [
            (self_intensity, impf_mdd, self_paa)
            for self_intensity, impf_mdd, self_paa
            in zip(self.intensity, impf.calc_mdr(self.mdd), self.paa)
        ]

        mapped_nodes_from_impf = [
            (self_intensity, impf_mdd, np.interp(impf_intensity, self.intensity, self.paa))
            for self_intensity, impf_intensity, impf_mdd
            in zip(self.invert_mdd(impf.intensity), impf.intensity, impf.mdd)
            if not np.isnan(self_intensity)
        ]

        df = pd.concat([
            pd.DataFrame(mapped_nodes_from_self, columns=['intensity', 'mdd', 'paa']),
            pd.DataFrame(mapped_nodes_from_impf, columns=['intensity', 'mdd', 'paa'])
        ]).sort_values(
            by=['intensity', 'mdd', 'paa']
        ).drop_duplicates()

        composed = ImpactFuncComposable(
            haz_type = self.haz_type,
            id = id if id else self.id,
            intensity = np.array(df['intensity']),
            mdd = np.array(df['mdd']),
            paa = np.array(df['paa']),
            intensity_unit = self.intensity_unit,
            name = name
        )
        composed.simplify()
        return composed


    def invert_mdd(self, to_invert):
        """
        Calculate the inverted values of the impact function.
        i.e. given a damage ratio, return the intensity that would cause it.
        Damage ratios must be monotonic
        """
        if not is_monotonic(self.mdd):
            raise ValueError("Can't invert an impact function where the MDD isn't monotonic")
        # Note: this will give slightly unexpected behaviour for step functions but we'll deal with them explicitly
        # elsewher
        # return -np.interp(to_invert, -self.mdd[::-1], -self.intensity[::-1], left=np.nan, right=np.nan)[::-1]
        return np.interp(to_invert, self.mdd, self.intensity, left=np.nan, right=np.nan)

    def simplify(self):
        gradient_mdd = [np.nan if dx == 0 else dy/dx for dy, dx in zip(np.diff(self.mdd), np.diff(self.intensity))]
        gradient_paa = [np.nan if dx == 0 else dy/dx for dy, dx in zip(np.diff(self.paa), np.diff(self.intensity))]
        keep_edge = ~np.multiply(np.diff(gradient_mdd) == 0, np.diff(gradient_paa) == 0) 
        keep_node = np.concatenate([np.array([True]), keep_edge, np.array([True])])
        self.intensity = self.intensity[keep_node]
        self.mdd = self.mdd[keep_node]
        self.paa = self.paa[keep_node]

    def get_step_indices(self):
        ix_intensity_steps = [
            i
            for i, (di, dm, dp) in enumerate(zip(np.diff(self.intensity), np.diff(self.mdd), np.diff(self.paa)))
            if di == 0 and (dm != 0 or dp !=0)
        ]
        ix_intensity_steps = set(ix_intensity_steps).union(set(ix_intensity_steps + 1))
        ix_intensity_steps = np.array(list(ix_intensity_steps))
        return ix_intensity_steps


def is_monotonic(v, only_increasing = False):
    dx = np.diff(v)
    if only_increasing:
        return np.all(dx >= 0)
    return (np.all(dx <= 0) or np.all(dx >= 0))