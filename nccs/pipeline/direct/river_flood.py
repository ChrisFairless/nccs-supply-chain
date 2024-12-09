"""
Class inspired by Climada ImpfTc
"""

__all__ = ['ImpfFlood']

import logging
import numpy as np

from climada.entity.impact_funcs.base import ImpactFunc

LOGGER = logging.getLogger(__name__)

class ImpfFlood(ImpactFunc):
    """Impact functions for flood."""

    def __init__(self):
        ImpactFunc.__init__(self)
        self.haz_type = 'RF'

    @classmethod
    def from_exp_sigmoid(cls, impf_id=1, intensity=np.arange(0.0, 12.0, 0.1),
                        v_half=0.5, translate=0):
        """
        RF impact function (2 / (1+np.exp(-intensity/scale_fact)))-1
        It has a single free parameter scale_fact which related to 
        v_half as scale_fact = v_half/ np.log(3)

        Parameters
        ----------
        impf_id : int, optional
            impact function id. Default: 1
        intensity : np.array, optional
            intensity array in m. Default:
            0.1m step array from 0 to 12m
        v_half : float, optional
            flood depth in meters
            at which 50% of max. damage is expected. Default:
            0.5

        Raises
        ------
        ValueError

        Returns
        -------
        impf : ImpfFlood
            RF impact function instance based on formula desribed above
        """
        if v_half <= 0:
            raise ValueError('v_half must be >0 ')

        impf = cls()
        impf.name = 'Exp sigmoid'
        impf.id = impf_id
        impf.intensity_unit = 'm'
        impf.intensity = intensity + translate
        impf.paa = np.ones(intensity.shape)
        scale_fact = v_half/ np.log(3)
        impf.mdd =(2 / (1+np.exp(-intensity/scale_fact)))-1
        return impf