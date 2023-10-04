import pycountry
import pandas as pd

from climada.util.api_client import Client
from climada.entity import ImpfTropCyclone, ImpactFuncSet
from climada.engine.impact_calc import ImpactCalc

#newly added
from CI_sectorial_exp.lonlat_to_country.step5_sectorial_exp_CI_MRIOT import sectorial_exp_CI_MRIOT

HAZ_TYPE_LOOKUP = {
    'tropical_cyclone': 'TC',
    'river_flood': 'RF'
}


# Method to loop through configuration lists of and run an impact calculation for 
# each combination on the list
# Simple, but can be sped up and memory usage reduced
def nccs_direct_impacts_list_simple(hazard_list, sector_list, country_list, scenario, ref_year):
    return pd.DataFrame(
        dict(
            haz_type=haz_type,
            sector=sector,
            country=country,
            scenario=scenario,
            ref_year=ref_year,
            impact_eventset=nccs_direct_impacts_simple(haz_type, sector, country, scenario, ref_year)
        )
        for haz_type in hazard_list for sector in sector_list for country in country_list
    )

def nccs_direct_impacts_simple(haz_type, sector, country, scenario, ref_year):
    country_iso3alpha = pycountry.countries.get(name=country).alpha_3
    haz = get_hazard(haz_type, country_iso3alpha, scenario, ref_year)
    exp = get_sector_exposure(sector, country) # was originally here
    #exp = sectorial_exp_CI_MRIOT(country=country_iso3alpha, sector=sector) #replaces the command above
    impf_set = get_sector_impf_set(haz_type, sector, country)
    return ImpactCalc(exp, impf_set, haz).impact(save_mat=True)



def get_sector_exposure(sector, country):
    if sector == 'service':
        client = Client()
        exp = client.get_litpop(country)
        exp.gdf['value'] = exp.gdf['value'] # / 100

    # add more sectors
    return exp


def get_sector_impf_set(hazard, sector, country):
    return ImpactFuncSet([get_sector_impf(hazard, sector, country)])


def get_sector_impf(hazard, sector, country):
    # TODO: load regional impfs based on country and
    # sector-specific impfs when they'll be available
    impf = ImpfTropCyclone.from_emanuel_usa()
    impf.haz_type = HAZ_TYPE_LOOKUP[hazard]
    return impf


def get_hazard(haz_type, country_iso3alpha, scenario, ref_year):
    client = Client()
    if haz_type == 'tropical_cyclone':
        return client.get_hazard(haz_type, properties={'country_iso3alpha': country_iso3alpha, 
                                                       'climate_scenario': scenario, 'ref_year': str(ref_year)})
    elif haz_type == 'river_flood':
        year_range_midpoint = round(ref_year/20) * 20
        year_range = str(year_range_midpoint - 10) + '_' + str(year_range_midpoint + 10)
        return client.get_hazard(haz_type, properties={'country_iso3alpha': country_iso3alpha, 
                                                       'climate_scenario': scenario, 'year_range': year_range})