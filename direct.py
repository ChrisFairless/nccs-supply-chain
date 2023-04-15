import pycountry
import numpy as np
import pandas as pd
from tqdm import tqdm

from climada.util.api_client import Client
from climada_petals.engine import SupplyChain
from climada.entity import ImpfTropCyclone, ImpactFuncSet, Exposures
from climada.engine.impact_calc import ImpactCalc

HAZ_TYPE_LOOKUP = {
    'tropical_cyclone': 'TC',
    'river_flood': 'RF'
}


# Method to loop through configuration lists of and run an impact calculation for each combination on the list
# Simple, but can be sped up.
def direct_impact_eventset_list_simple(hazard_list, sector_list, country_list, scenario, ref_year):
    return pd.DataFrame(
        dict(
            haz_type=haz_type,
            sector=sector,
            country=country,
            scenario=scenario,
            ref_year=ref_year,
            impact=direct_impact_eventset_simple(haz_type, sector, country, scenario, ref_year)
        )
        for haz_type in hazard_list for sector in sector_list for country in country_list
    )

def direct_impact_eventset_simple(haz_type, sector, country, scenario, ref_year):
    country_iso3alpha = pycountry.countries.get(name=country).alpha_3
    haz = get_hazard(haz_type, country_iso3alpha, scenario, ref_year)
    exp = get_sector_exposure(sector, country)
    impf_set = get_sector_impf_set(haz_type, sector, country)
    return ImpactCalc(exp, impf_set, haz).impact(save_mat=True)


def get_sector_exposure(sector, country):
    if sector[0:6] == 'litpop':
        scaling = float(sector[7:])
        client = Client()
        exp = client.get_litpop(country)
        exp.gdf['value'] = exp.gdf['value'] * scaling / 100
        return exp
    else:
        raise ValueError('So far we only work with LitPop exposures')


def get_sector_impf_set(hazard, sector, country):
    return ImpactFuncSet([get_sector_impf(hazard, sector, country)])


def get_sector_impf(hazard, sector, country):
    impf = ImpfTropCyclone.from_emanuel_usa()
    impf.haz_type = HAZ_TYPE_LOOKUP[hazard]
    return impf


def get_hazard(haz_type, country_iso3alpha, scenario, ref_year):
    client = Client()
    if haz_type == 'tropical_cyclone':
        return client.get_hazard(haz_type, properties={'country_iso3alpha': country_iso3alpha, 'climate_scenario': scenario, 'ref_year': str(ref_year)})
    elif haz_type == 'river_flood':
        year_range_midpoint = round(ref_year/20) * 20
        year_range = str(year_range_midpoint - 10) + '_' + str(year_range_midpoint + 10)
        return client.get_hazard(haz_type, properties={'country_iso3alpha': country_iso3alpha, 'climate_scenario': scenario, 'year_range': year_range})