import typing

import numpy as np
from climada.entity import ImpactFunc
from climada.entity import ImpactFuncSet
from climada.util.api_client import Client
from climada_petals.entity.impact_funcs.relative_cropyield import ImpfRelativeCropyield
from pycountry import countries

CropType = typing.Literal[
    "whe",
    "mai",
    "soy",
    "ric",
]
IrrigationType = typing.Literal["firr", "noirr"]


def split_agriculture_hazard(label):
    """ Parses a label like 'relative_crop_yield_whe' into its components. """
    hazard = "relative_crop_yield"
    crop_type = label.replace("relative_crop_yield_", "")
    return hazard, crop_type


def split_agriculture_sector(label):
    """ Parses a label like 'agriculture_whe' into its components. """
    sector = "agriculture"
    crop_type = label.replace("agriculture_", "")
    return sector, crop_type


def get_exposure(crop_type: CropType = "whe", scenario="histsoc", irr: IrrigationType = "firr"):
    client = Client()
    return client.get_exposures(
        "crop_production", properties={
            "irrigation_status": irr,
            "crop": crop_type,
            "unit": "USD"
        }
    )


def get_impf_set(crop_type: typing.Union[CropType, None] = None):
    # TODO: check if other impact functions are needed
    impf_cp = ImpactFuncSet()
    impf_def = ImpfRelativeCropyield()
    impf_def.set_relativeyield()
    impf_cp.append(impf_def)
    impf_cp.check()
    return impf_cp


def get_impf_set_tc():
    imp_fun_maize = ImpactFunc(
        id=1,
        name="TC agriculture damage",
        intensity_unit="m/s",
        haz_type="TC",
        intensity=np.array([0, 11, 38, 60]),
        mdd=np.array([0, 0, 1, 1]),
        paa=np.array([1, 1, 1, 1])
    )
    imp_fun_maize.check()
    imp_fun_set = ImpactFuncSet([imp_fun_maize])
    return imp_fun_set


def get_hazard(
        country,
        year_range,
        scenario: typing.Literal["historical", "rcp60"] = "historical",
        crop_type: CropType = "whe",  # mai instead of wheat
        irr: IrrigationType = "firr"):
    # TODO how to map the year to the years in this model
    # TODO What about the firr and noirr?
    client = Client()
    hazard = client.get_hazard(
        "relative_cropyield",
        properties={
            'climate_scenario': scenario,
            'crop': crop_type,
            'irrigation_status': irr,
            'year_range': year_range
        }
    )
    if hasattr(hazard.centroids, 'gdf') and np.all(
            hazard.centroids.region_id == 1
    ):  # if the region ids exist but are all 1 (happens in newer climada)
        hazard.centroids.gdf.region_id = np.nan
    hazard.centroids.set_region_id()
    region_id = int(countries.get(alpha_3=country).numeric)
    return hazard.select(reg_id=region_id)
