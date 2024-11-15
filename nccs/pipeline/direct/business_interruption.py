from pathlib import Path
import pandas as pd
import numpy as np
import pycountry
import logging
import os
from climada.entity import ImpactFunc
from nccs.utils.folder_naming import get_resources_dir
from nccs.pipeline.direct.combine_impact_funcs import ImpactFuncComposable

SECTOR_BI_DRY_PATH = Path(get_resources_dir(), 'impact_functions', 'business_interruption', 'TC_HAZUS_BI_industry_modifiers_v2.csv')
SECTOR_BI_WET_PATH = Path(get_resources_dir(), 'impact_functions', 'business_interruption', 'FL_HAZUS_BI_industry_modifiers.csv')
SECTOR_BI_WET_SCALE_PATH = Path(get_resources_dir(), 'impact_functions', 'business_interruption', 'bi_scaling_regional.csv')

SECTOR_MAPPING = {
    "agriculture": "Agriculture",
    "forestry": "Forestry",
    "mining": "Mining (Processing)",
    "manufacturing": "Manufacturing",
    "service": "Service",
    "utilities": "Utilities",
    "energy": "Utilities",
    "water": "Utilities",
    "waste": "Utilities",
    "basic_metals": "Mining (Processing)",
    "pharmaceutical": "Manufacturing",
    "food": "Manufacturing",
    "wood": "Manufacturing",
    "chemical": "Manufacturing",
    "rubber_and_plastic": "Manufacturing",
    "non_metallic_mineral": "Mining (Processing)",
    "refin_and_transform": "Manufacturing"
}

def get_sector_bi_dry(sector, country_iso3alpha):

    #TODO include the regional bi-scaling here too (not yet implemented as we do not have the scaling yet for dry)
    bi_sector = SECTOR_MAPPING[sector]
    bi = pd.read_csv(SECTOR_BI_DRY_PATH).set_index(['Industry Type']).loc[bi_sector]
    if np.max(bi.values) > 1:
        logging.warning(f'The {sector} business interruption function ({bi_sector} in the HAZUS tables) has values > 1. Capping at 1 for now.')

    return ImpactFunc(
        haz_type='BI',
        id=1,
        intensity=np.array(bi.index).astype(float),
        mdd=np.minimum(1, bi.values * float(os.environ.get('BI_CALIBRATION_SCALE', 1.0))),
        paa=np.ones_like(bi.values * float(os.environ.get('BI_CALIBRATION_SCALE', 1.0))),
        intensity_unit="",
        name="Business interruption: " + sector
    )

def get_sector_bi_wet(sector, country_iso3alpha):
    bi_sector = SECTOR_MAPPING[sector]
    bi = pd.read_csv(SECTOR_BI_WET_PATH).set_index(['Industry Type']).loc[bi_sector]
    #map the iso code back to a country
    country = pycountry.countries.get(alpha_3=country_iso3alpha).name
    #get the factor from the csv
    country_scale = (pd.read_csv(SECTOR_BI_WET_SCALE_PATH)[(lambda df: (df['country'] == country))])
    factor= country_scale.iloc[0]['normalized_NA'] if not country_scale.empty else None

    if np.max(bi.values) > 1:
        logging.warning(f'The {sector} business interruption function ({bi_sector} in the HAZUS tables) has values > 1. Capping at 1 for now.')

    return ImpactFunc(
        haz_type='BI',
        id=1,
        intensity=np.array(bi.index).astype(float),
        # mdd=np.minimum(1, bi.values * float(os.environ.get('BI_CALIBRATION_SCALE', 1.0))), #used when calibration run
        # paa=np.ones_like(bi.values * float(os.environ.get('BI_CALIBRATION_SCALE', 1.0))), #used when calibration run
        mdd=np.minimum(1, bi.values * float(factor)),
        paa=np.ones_like(bi.values * float(factor)),
        intensity_unit="",
        name="Business interruption: " + sector
    )

# TODO add BI regional modifiers for the dry function similar to wet (add country_iso3alpha here too)
def convert_impf_to_sectoral_bi_dry(impf, sector, id=1):
    impf_bi = get_sector_bi_dry(sector)
    return ImpactFuncComposable.from_impact_funcs(
        impf_list = [impf, impf_bi],
        id = id,
        name = f'Business interruption: {impf.haz_type} and {sector}',
        enforce_unit_interval_impacts = True

    )

def convert_impf_to_sectoral_bi_wet(impf, sector, country_iso3alpha, id=1):
    impf_bi = get_sector_bi_wet(sector, country_iso3alpha)
    return ImpactFuncComposable.from_impact_funcs(
        impf_list = [impf, impf_bi],
        id = id,
        name = f'Business interruption: {impf.haz_type} and {sector}',
        enforce_unit_interval_impacts = True
    )