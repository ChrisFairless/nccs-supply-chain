import typing

import numpy as np
import pandas as pd
from climada.entity import Exposures, ImpactFunc
from climada.entity import ImpactFuncSet
from climada.util.api_client import Client
from climada_petals.entity.impact_funcs.relative_cropyield import ImpfRelativeCropyield
from climada_petals.entity.impact_funcs.river_flood import RIVER_FLOOD_REGIONS_CSV
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


def get_exposure(country, crop_type: CropType = "whe", scenario="histsoc", irr: IrrigationType = "firr"):
    client = Client()

    exp = client.get_exposures(
        "crop_production", properties={
            "irrigation_status": irr,
            "crop": crop_type,
            "unit": "USD"
        }
    )
    region_id = int(countries.get(name=country).numeric)
    return Exposures(data=exp.gdf[exp.gdf['region_id'] == region_id])


def get_impf_set(crop_type: typing.Union[CropType, None] = None):
    # TODO: check if other impact functions are needed
    impf_cp = ImpactFuncSet()
    impf_def = ImpfRelativeCropyield.impf_relativeyield()

    # Invert the impact function to match the expected behavior
    impf_def.mdd = -impf_def.mdd

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



def get_impf_set_rf(country_iso3alpha, haz_type="RF"):
    """
    New Impact function set for river flood and agriculture for specified region in the world

    Based on the JRC publication: https://publications.jrc.ec.europa.eu/repository/handle/JRC105688

    Regional functions available for Africa, Europe, North America, and Asia

    Other regions (Oceania and South America will get the Global function assigned)

    In this study the damage fractions in the damage curves are intended to span from zero
    (no damage) to one (maximum damage).

    For agriculture the damage is related to a loss in output when the yield is destroyed by floods.



    """

    # Use the flood module's lookup to get the regional impact function for the country
    country_info = pd.read_csv(RIVER_FLOOD_REGIONS_CSV)
    impf_id = country_info.loc[country_info['ISO'] == country_iso3alpha, 'impf_RF'].values[0]

    if impf_id == 1:
        impf = ImpactFunc(
            id = 1,
            name = "Flood Africa JRC Agriculture",
            intensity_unit="m",
            haz_type=haz_type,
            intensity = np.array([0, 0.5, 1, 1.5, 2, 3, 4, 5, 6]),
            mdd = np.array([0.00, 0.24, 0.47, 0.74, 0.92, 1.00, 1.00,
                            1.00, 1.00]),
            paa = np.array([1, 1, 1, 1, 1, 1, 1,
                            1, 1])
        )


    elif impf_id == 2:
        impf = ImpactFunc(
            id = 1,
            name = "Flood Asia JRC Agriculture",
            intensity_unit="m",
            haz_type=haz_type,
            intensity = np.array([0, 0.5, 1, 1.5, 2, 3, 4, 5, 6]),
            mdd = np.array([0.00, 0.14, 0.37, 0.52, 0.56, 0.66, 0.83,
                            0.99, 1.00]),
            paa = np.array([1, 1, 1, 1, 1, 1, 1,
                            1, 1])
        )



    elif impf_id == 3:
        impf = ImpactFunc(
            id = 1,
            name = "Flood Europe JRC Agriculture",
            intensity_unit="m",
            haz_type=haz_type,
            intensity = np.array([0, 0.5, 1, 1.5, 2, 3, 4, 5, 6]),
            mdd = np.array([0.00, 0.30, 0.55, 0.65, 0.75, 0.85, 0.95,
                            1.00, 1.00]),
            paa = np.array([1, 1, 1, 1, 1, 1, 1,
                            1, 1])
        )


    elif impf_id == 4:
        impf = ImpactFunc(
            id = 1,
            name = "Flood North America JRC Agriculture",
            intensity_unit="m",
            haz_type=haz_type,
            intensity = np.array([0, 0.01, 0.5, 1, 1.5, 2, 3, 4, 5, 6]),
            mdd = np.array([0, 0.02, 0.27, 0.47, 0.55, 0.60, 0.76, 0.87,
                            0.95, 1.00]),
            paa = np.array([1, 1, 1, 1, 1, 1, 1, 1,
                            1, 1])
        )

    else:
        impf = ImpactFunc(
            id=1,
            name = "Flood Global JRC Agriculture",
            intensity_unit="m",
            haz_type=haz_type,
            intensity = np.array([0, 0.5, 1, 1.5, 2, 3, 4, 5, 6]),
            mdd = np.array([0.00, 0.24, 0.47, 0.62, 0.71, 0.82, 0.91,
                            0.99, 1.00]),
            paa = np.array([1, 1, 1, 1, 1, 1, 1,
                            1, 1])
        )


    impf.check()

    return ImpactFuncSet([impf])



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
    hazard = hazard.select(reg_id=region_id)
    return hazard
