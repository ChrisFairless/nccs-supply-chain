# for the wilfire impact function:
# /climada_petals/blob/main/climada_petals/entity/impact_funcs/wildfire.py

import pandas as pd
import pycountry
from climada.engine.impact_calc import ImpactCalc
from climada.entity import Exposures
from climada.entity import ImpactFuncSet, ImpfTropCyclone
from climada.entity.impact_funcs.storm_europe import ImpfStormEurope
from climada.util.api_client import Client
from climada_petals.entity.impact_funcs.river_flood import RIVER_FLOOD_REGIONS_CSV, flood_imp_func_set
# for the wilfire impact function:
from climada_petals.entity.impact_funcs.wildfire import \
    ImpfWildfire  # https://github.com/CLIMADA-project/climada_petals/blob/main/climada_petals/entity/impact_funcs

import agriculture
import h5py
import pickle

# /wildfire.py

# newly added

HAZ_TYPE_LOOKUP = {
    'tropical_cyclone': 'TC',
    'river_flood': 'RF',
    'wildfire': 'WF',
    'storm_europe': 'WS',
    "relative_crop_yield": "RC",
}

WS_SCENARIO_LOOKUP = {
    'rcp26': 'ssp126',
    'rcp45': 'ssp245',
    'rcp60': 'ssp370',  # TODO check this is acceptable
    'rcp85': 'ssp585'
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
        input_file = 'exposures/mining_500_exposure.xlsx'
        excel_data = pd.read_excel(input_file)
        # Generate an Exposures instance from DataFrame
        exp = Exposures(excel_data)
        exp.set_geometry_points()
        exp.gdf['value'] = exp.gdf.value
        exp.check()

    if sector == 'electricity':
        # load an exposure from an excel file
        input_file = 'exposures/utilities_power_plant_global_database_WRI.xlsx'
        excel_data = pd.read_excel(input_file)
        # Generate an Exposures instance from DataFrame
        exp = Exposures(excel_data)
        exp.set_geometry_points()
        exp.gdf['value'] = exp.gdf.value
        exp.check()

    if sector == 'agriculture':
        exp = agriculture.get_exposure(crop_type="whe", scenario="histsoc", irr="firr")

    if sector == 'forestry':
        try:
            # open this exposure file from the pickle
            with open("exposures/forestry/exp_forestry.pkl", "rb") as f:
                exp = pickle.load(f)
                exp.check()
        except:
            # load an exposure from a hdf5 file
            input_file_forest = 'exposures/forestry/forest_exp_region.h5'
            h5_file = pd.read_hdf(input_file_forest)
            # Generate an Exposures instance from DataFrame
            exp = Exposures(h5_file)
            exp.set_geometry_points()
            exp.gdf['value'] = exp.gdf.value
            exp.check()
            """
            Save this exposure into an intermediate file format to use it in a later code
            use therefore the picke thing
            """
            with open("exposures/forestry/exp_forestry.pkl", "wb") as f:
                pickle.dump(exp, f)


    return exp


def apply_sector_impf_set(hazard, sector, country_iso3alpha):
    haz_type = HAZ_TYPE_LOOKUP[hazard]

    if haz_type == 'TC' and sector=='agriculture':
        return agriculture.get_impf_set_TC()
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
    impf.haz_type = 'WFseason' #TODO there is a warning when running the code that the haz_type is set to WFsingle
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
                #'climate_scenario': WS_SCENARIO_LOOKUP[scenario]
                'climate_scenario': scenario
            }
        )
        # TODO filter to bounding box
    # TODO currently always returns the same hazard

    elif haz_type == "relative_crop_yield":
        # TODO currently always returns the same hazard
        if scenario == 'None' and ref_year=="historical":
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
        raise ValueError(f'Unrecognised haz_type variable: {haz_type}.\nPlease use one of: {list(HAZ_TYPE_LOOKUP.keys())}')
