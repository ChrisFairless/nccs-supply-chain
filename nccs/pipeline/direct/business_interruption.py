from pathlib import Path
import pandas as pd
import numpy as np
import logging
import os
from climada.entity import ImpactFunc
from nccs.utils.folder_naming import get_resources_dir
from nccs.pipeline.direct.combine_impact_funcs import ImpactFuncComposable

SECTOR_BI_DRY_PATH = Path(get_resources_dir(), 'impact_functions', 'business_interruption', 'TC_HAZUS_BI_industry_modifiers_v2.csv')
SECTOR_BI_WET_PATH = Path(get_resources_dir(), 'impact_functions', 'business_interruption', 'FL_HAZUS_BI_industry_modifiers.csv')
SECTOR_BI_WET_SCALE_PATH = Path(get_resources_dir(), 'impact_functions', 'business_interruption', 'FL_HAZUS_BI_regional_modifiers_scale.csv')

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
    bi_sector = SECTOR_MAPPING[sector]
    bi = pd.read_csv(SECTOR_BI_DRY_PATH).set_index(['Industry Type']).loc[bi_sector]
    if np.max(bi.values) > 1:
        logging.warning(f'The {sector} business interruption function ({bi_sector} in the HAZUS tables) has values > 1. Capping at 1 for now.')

    # TODO Alina: Add the scaling factor here by reading it from the file

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
    if np.max(bi.values) > 1:
        logging.warning(f'The {sector} business interruption function ({bi_sector} in the HAZUS tables) has values > 1. Capping at 1 for now.')

    # TODO Alina: Add the scaling factor here by reading it from the file
    return ImpactFunc(
        haz_type='BI',
        id=1,
        intensity=np.array(bi.index).astype(float),
        mdd=np.minimum(1, bi.values * float(os.environ.get('BI_CALIBRATION_SCALE', 1.0))),
        paa=np.ones_like(bi.values * float(os.environ.get('BI_CALIBRATION_SCALE', 1.0))),
        intensity_unit="",
        name="Business interruption: " + sector
    )


def convert_impf_to_sectoral_bi_dry(impf, sector, country_iso3alpha, id=1):
    impf_bi = get_sector_bi_dry(sector, country_iso3alpha)
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