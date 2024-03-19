# for the wilfire impact function:
# /climada_petals/blob/main/climada_petals/entity/impact_funcs/wildfire.py

from utils.folder_naming import get_resource_dir
from functools import cache

import pandas as pd
import pycountry
from climada.engine.impact_calc import ImpactCalc
from climada.entity import Exposures
from climada.entity import ImpactFuncSet, ImpfTropCyclone
from climada.entity.impact_funcs.storm_europe import ImpfStormEurope
from climada.util.api_client import Client
from climada_petals.entity.impact_funcs.river_flood import RIVER_FLOOD_REGIONS_CSV, flood_imp_func_set
from utils.s3client import download_from_s3_bucket
from exposures.utils import root_dir

# for the wilfire impact function:
# https://github.com/CLIMADA-project/climada_petals/blob/main/climada_petals/entity/impact_funcs
from climada_petals.entity.impact_funcs.wildfire import ImpfWildfire

import pipeline.direct.agriculture as agriculture

project_root = root_dir()
# /wildfire.py

# newly added

HAZ_TYPE_LOOKUP = {
    'tropical_cyclone': 'TC',
    'river_flood': 'RF',
    'wildfire': 'WF',
    'storm_europe': 'WS',
    "relative_crop_yield": "RC",
}


# Method to loop through configuration lists of and run an impact calculation for 
# each combination on the list
# Simple, but can be sped up and memory usage reduced
def nccs_direct_impacts_list_simple(hazard_list, sector_list, country_list, scenario, ref_year):
    result = []
    for haz_type in hazard_list:
        for sector in sector_list:
            for country in country_list:
                try:
                    # This could fail if a hazard is not available for a certain country or sector
                    result.append(
                        dict(
                            haz_type=haz_type,
                            sector=sector,
                            country=country,
                            scenario=scenario,
                            ref_year=ref_year,
                            impact_eventset=nccs_direct_impacts_simple(haz_type, sector, country, scenario, ref_year)
                        )
                    )
                except Exception as e:
                    print(f"Error calculating direct impacts for {country} {sector} {haz_type}: {e}")

    return pd.DataFrame(result)


def nccs_direct_impacts_simple(haz_type, sector, country, scenario, ref_year):
    # Country names can be checked here: https://github.com/flyingcircusio/pycountry/blob/main/src/pycountry
    # /databases/iso3166-1.json
    print(f"Calculating direct impacts for {country} {sector} {haz_type} {scenario} {ref_year}")
    country_iso3alpha = pycountry.countries.get(name=country).alpha_3
    haz = get_hazard(haz_type, country_iso3alpha, scenario, ref_year)
    exp = get_sector_exposure(sector, country)  # was originally here
    # exp = sectorial_exp_CI_MRIOT(country=country_iso3alpha, sector=sector) #replaces the command above
    impf_set = apply_sector_impf_set(haz_type, sector, country_iso3alpha)
    return ImpactCalc(exp, impf_set, haz).impact(save_mat=True)


@cache
def load_forestry_exposure():
    # Load an exposure from an hdf5 file
    input_file_forest = f'{get_resource_dir()}/forestry/best_guesstimate/forestry_values_MRIO_avg(upd_2).h5'
    h5_file = pd.read_hdf(input_file_forest)
    # Generate an Exposures instance from DataFrame
    exp = Exposures(h5_file)
    exp.set_geometry_points()
    exp.gdf['value'] = exp.gdf.value
    exp.check()
    return exp

#TODO implemement a general function to open the subexposures splitted in countries
#TODO implement load statements from the s3 bucket
def load_manufacturing_exposure(country, sector):
    country_iso3alpha = pycountry.countries.get(name=country).alpha_3
    # Load an exposure from a hdf5 file
    input_file_forest = f'resources/exposures/manufacturing/{sector}_NOx_emissions_2011_above_100t_0.1deg_ISO3_values_Manfac_scaled_{country_iso3alpha}.h5'
    h5_file = pd.read_hdf(input_file_forest)
    # Generate an Exposures instance from DataFrame
    exp = Exposures(h5_file)
    exp.set_geometry_points()
    exp.gdf['value'] = exp.gdf.value
    exp.check()
    return exp

def download_exposure_from_s3(country, sector, file_short):
    country_iso3alpha = pycountry.countries.get(name=country).alpha_3
    s3_filepath = f'exposures/{sector}/{file_short}_{country_iso3alpha}.h5'
    outputfile=f'{project_root}/exposures/{sector}/{file_short}_{country_iso3alpha}.h5'
    download_from_s3_bucket(s3_filepath, outputfile)
    h5_file = pd.read_hdf(outputfile)
    # Generate an Exposures instance from DataFrame
    exp = Exposures(h5_file)
    exp.set_geometry_points()
    exp.gdf['value'] = exp.gdf.value
    exp.check()
    return exp

def download_sub_exposure_from_s3(country, sector, file_short):
    country_iso3alpha = pycountry.countries.get(name=country).alpha_3
    s3_filepath = f'exposures/{file_short}_{country_iso3alpha}.h5'
    outputfile=f'{project_root}/exposures/{file_short}_{country_iso3alpha}.h5'
    download_from_s3_bucket(s3_filepath, outputfile)
    h5_file = pd.read_hdf(outputfile)
    # Generate an Exposures instance from DataFrame
    exp = Exposures(h5_file)
    exp.set_geometry_points()
    exp.gdf['value'] = exp.gdf.value
    exp.check()
    return exp




def get_sector_exposure(sector, country):
    if sector == 'service':
        client = Client()
        exp = client.get_litpop(country)
        exp.gdf['value'] = exp.gdf['value']  # / 100

    if sector == 'manufacturing':
        client = Client()
        exp = client.get_litpop(country)  # first guess with litpop
        exp.gdf['value'] = exp.gdf['value']  # / 100
    # add more sectors
    if sector == 'mining':
        # load an exposure from an excel file
        input_file = f'{get_resource_dir()}/mining/best_guesstimate/mining_500_exposure.xlsx'
        excel_data = pd.read_excel(input_file)
        # Generate an Exposures instance from DataFrame
        exp = Exposures(excel_data)
        exp.set_geometry_points()
        exp.gdf['value'] = exp.gdf.value
        exp.check()

    if sector == 'electricity':
        # load an exposure from an excel file
        input_file = f'{get_resource_dir()}/utilities/best_guesstimate/utilities_power_plant_global_database_WRI.xlsx'
        excel_data = pd.read_excel(input_file)
        # Generate an Exposures instance from DataFrame
        exp = Exposures(excel_data)
        exp.set_geometry_points()
        exp.gdf['value'] = exp.gdf.value
        exp.check()

    if sector == 'agriculture':
        exp = agriculture.get_exposure(crop_type="whe", scenario="histsoc", irr="firr")

    if sector == 'forestry':
        exp = load_forestry_exposure()

    if sector == 'pharmaceutical':
        file_short = f'manufacturing/manufacturing_sub_exposures/refinement_1/{sector}/country_split/pharmaceutical_NMVOC_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled'
        exp = download_sub_exposure_from_s3(country, sector, file_short)

    return exp


def apply_sector_impf_set(hazard, sector, country_iso3alpha):
    haz_type = HAZ_TYPE_LOOKUP[hazard]

    if haz_type == 'TC' and sector == 'agriculture':
        return agriculture.get_impf_set_tc()
    if haz_type == 'TC':
        return ImpactFuncSet([get_sector_impf_tc(country_iso3alpha)])
    if haz_type == 'RF':
        return ImpactFuncSet([get_sector_impf_rf(country_iso3alpha)])
    if haz_type == 'WF':
        return ImpactFuncSet([get_sector_impf_wf()])
    if haz_type == 'WS':
        return ImpactFuncSet([get_sector_impf_ws()])
    if haz_type == 'RC':
        return agriculture.get_impf_set()
    Warning('No impact functions defined for this hazard. Using TC impact functions just so you have something')
    return ImpactFuncSet([get_sector_impf_tc(country_iso3alpha, haz_type)])


def get_sector_impf_tc(country_iso3alpha, haz_type='TC'):
    # TODO: load regional impfs based on country and
    impf = ImpfTropCyclone.from_emanuel_usa()
    impf.haz_type = haz_type
    return impf


def get_sector_impf_rf(country_iso3alpha):
    # Use the flood module's lookup to get the regional impact function for the country
    country_info = pd.read_csv(RIVER_FLOOD_REGIONS_CSV)
    impf_id = country_info.loc[country_info['ISO'] == country_iso3alpha, 'impf_RF'].values[0]
    # Grab just that impact function from the flood set, and set its ID to 1
    impf_set = flood_imp_func_set()
    impf = impf_set.get_func(haz_type='RF', fun_id=impf_id)
    impf.id = 1
    return impf


# for wildfire, not sure if it is working
def get_sector_impf_wf():
    impf = ImpfWildfire.from_default_FIRMS()
    impf.haz_type = 'WFseason'  # TODO there is a warning when running the code that the haz_type is set to WFsingle, but if I set it to WFsingle, the code does not work
    return impf


def get_sector_impf_ws():
    impf = ImpfStormEurope.from_schwierz()
    return impf


def get_hazard(haz_type, country_iso3alpha, scenario, ref_year):
    client = Client()
    if haz_type == 'tropical_cyclone':

        if scenario == 'None' and ref_year == 'historical':

            return client.get_hazard(
                haz_type, properties={
                    'country_iso3alpha': country_iso3alpha,
                    'climate_scenario': 'None',
                    'event_type': 'synthetic'
                }
            )
        else:
            return client.get_hazard(
                haz_type, properties={
                    'country_iso3alpha': country_iso3alpha,
                    'climate_scenario': scenario, 'ref_year': str(ref_year)
                }
            )
    elif haz_type == 'river_flood':
        if scenario == 'None' and ref_year == 'historical':
            return client.get_hazard(
                haz_type, properties={
                    'country_iso3alpha': country_iso3alpha,
                    'climate_scenario': 'historical', 'year_range': '1980_2000'
                }
            )
        else:
            year_range_midpoint = round(ref_year / 20) * 20
            year_range = str(year_range_midpoint - 10) + '_' + str(year_range_midpoint + 10)
            return client.get_hazard(
                haz_type, properties={
                    'country_iso3alpha': country_iso3alpha,
                    'climate_scenario': scenario, 'year_range': year_range
                }
            )
    elif haz_type == 'wildfire':
        year_range = '2001_2020'
        if scenario == 'None' and ref_year == 'historical':
            return client.get_hazard(
                haz_type, properties={
                    'country_iso3alpha': country_iso3alpha,
                    'climate_scenario': 'historical', 'year_range': year_range
                }
            )
    elif haz_type == "storm_europe":
        return client.get_hazard(
            haz_type, properties={
                'spatial_coverage': 'Europe',
                'gcm': 'EC-Earth3-Veg',
                'climate_scenario': scenario
            }
        )
        # TODO filter to bounding box
    # TODO currently always returns the same hazard

    elif haz_type == "relative_crop_yield":
        # TODO currently always returns the same hazard
        if scenario == 'None' and ref_year == "historical":
            return agriculture.get_hazard(
                country=country_iso3alpha,
                year_range="1971_2001",
                scenario="historical"
            )
        else:
            return agriculture.get_hazard(
                country=country_iso3alpha,
                year_range=ref_year,
                scenario=scenario
            )
    else:
        raise ValueError(
            f'Unrecognised haz_type variable: {haz_type}.\nPlease use one of: {list(HAZ_TYPE_LOOKUP.keys())}'
        )
