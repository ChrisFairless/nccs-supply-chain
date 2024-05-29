# for the wilfire impact function:
# /climada_petals/blob/main/climada_petals/entity/impact_funcs/wildfire.py

from utils.folder_naming import get_resource_dir
from functools import cache
import pandas as pd
import pycountry

from climada.engine.impact_calc import ImpactCalc
from climada.entity import Exposures
from climada.entity import ImpactFuncSet, ImpfTropCyclone, ImpfSetTropCyclone
from climada.entity.impact_funcs.storm_europe import ImpfStormEurope
from climada.util.api_client import Client
from climada_petals.entity.impact_funcs.river_flood import RIVER_FLOOD_REGIONS_CSV, flood_imp_func_set
from utils.s3client import download_from_s3_bucket
from exposures.utils import root_dir

# for the wilfire impact function:
# https://github.com/CLIMADA-project/climada_petals/blob/main/climada_petals/entity/impact_funcs
from climada_petals.entity.impact_funcs.wildfire import ImpfWildfire

from pipeline.direct import agriculture, stormeurope
from pipeline.direct.business_interruption import convert_impf_to_sectoral_bi


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
                    #raise e

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


# @cache
# def load_forestry_exposure():
#     # Load an exposure from an hdf5 file
#     input_file_forest = f'{get_resource_dir()}/forestry/best_guesstimate/forestry_values_MRIO_avg(upd_2).h5'
#     h5_file = pd.read_hdf(input_file_forest)
#     # Generate an Exposures instance from DataFrame
#     exp = Exposures(h5_file)
#     exp.set_geometry_points()
#     exp.gdf['value'] = exp.gdf.value
#     exp.check()
#     return exp


def download_exposure_from_s3(country,file_short):
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
    """
    There are now commeneted versions that worked previously only locally, as the files were not synched. The best guesstimate
    results are now also availabe in the s3 bucket and could be selected by changing the file path to the s3 bucket
    would require to create a new donwload function, as for instance the mining file is an xlsx and would not work with the opening command
    """

    if sector == 'service':
        client = Client()
        exp = client.get_litpop(country)
        exp.gdf['value'] = exp.gdf['value']  # / 100

    if sector == 'manufacturing':
        # best guesstimate run used this:
        # client = Client()
        # exp = client.get_litpop(country)  # first guess with litpop
        # exp.gdf['value'] = exp.gdf['value']  # / 100

        #current active version
        file_short = f'manufacturing/manufacturing_general_exposure/refinement_1/country_split/global_noxemissions_2011_above_100t_0.1deg_ISO3_values_Manfac_scaled'
        exp = download_exposure_from_s3(country,  file_short)

    if sector == 'mining':
        # best guesstimate run used this:
        # # load an exposure from an excel file
        # input_file = f'{get_resource_dir()}/mining/best_guesstimate/mining_500_exposure.xlsx'
        # excel_data = pd.read_excel(input_file)
        # # Generate an Exposures instance from DataFrame
        # exp = Exposures(excel_data)
        # exp.set_geometry_points()
        # exp.gdf['value'] = exp.gdf.value
        # exp.check()

        file_short = f'{sector}/refinement_1/country_split/global_miningarea_v2_30arcsecond_converted_ISO3_improved_values_MP_scaled'
        exp = download_exposure_from_s3(country,  file_short)

        #only used for best guesstimate
    # if sector == 'electricity':
    #     # load an exposure from an excel file
    #     input_file = f'{get_resource_dir()}/utilities/best_guesstimate/utilities_power_plant_global_database_WRI.xlsx'
    #     excel_data = pd.read_excel(input_file)
    #     # Generate an Exposures instance from DataFrame
    #     exp = Exposures(excel_data)
    #     exp.set_geometry_points()
    #     exp.gdf['value'] = exp.gdf.value
    #     exp.check()

    if sector == 'agriculture':
        exp = agriculture.get_exposure(crop_type="whe", scenario="histsoc", irr="firr")

    if sector == 'forestry':
        # exp = load_forestry_exposure() #only used for best guesstimate
        file_short = f'forestry/refinement_1/country_split/{sector}_values_MRIO_avg(WB-v2)'
        exp = download_exposure_from_s3(country,  file_short)

    #Utilities
    if sector == 'energy':
        file_short = f'utilities/refinement_1/Subscore_{sector}/country_split/Subscore_{sector}_MRIO'
        exp = download_exposure_from_s3(country,  file_short)

    if sector == 'waste':
        file_short = f'utilities/refinement_1/Subscore_{sector}/country_split/Subscore_{sector}_MRIO'
        exp = download_exposure_from_s3(country,  file_short)

    if sector == 'water':
        file_short = f'utilities/refinement_1/Subscore_{sector}/country_split/Subscore_{sector}_MRIO'
        exp = download_exposure_from_s3(country,  file_short)

    #raw materials
    if sector == 'pharmaceutical':
        file_short = f'manufacturing/manufacturing_sub_exposures/refinement_1/{sector}/country_split/{sector}_NMVOC_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled'
        exp = download_exposure_from_s3(country,  file_short)

    if sector == 'basic_metals':
        file_short = f'manufacturing/manufacturing_sub_exposures/refinement_1/{sector}/country_split/{sector}_CO_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled'
        exp = download_exposure_from_s3(country,  file_short)

    if sector == 'chemical':
        file_short = f'manufacturing/manufacturing_sub_exposures/refinement_1/{sector}_process/country_split/{sector}_process_NMVOC_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled'
        exp = download_exposure_from_s3(country,  file_short)

    if sector == 'food':
        file_short = f'manufacturing/manufacturing_sub_exposures/refinement_1/{sector}_and_paper/country_split/{sector}_and_paper_NOX_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled'
        exp = download_exposure_from_s3(country,  file_short)

    if sector == 'non_metallic_mineral':
        file_short = f'manufacturing/manufacturing_sub_exposures/refinement_1/{sector}/country_split/{sector}_PM10_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled'
        exp = download_exposure_from_s3(country, file_short)

    if sector == 'refin_and_transform':
        file_short = f'manufacturing/manufacturing_sub_exposures/refinement_1/{sector}/country_split/{sector}_NOx_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled'
        exp = download_exposure_from_s3(country, file_short)

    if sector == 'rubber_and_plastic':
        file_short = f'manufacturing/manufacturing_sub_exposures/refinement_1/{sector}/country_split/{sector}_NOx_emissions_2011_above_100t_0.1deg_ISO3_values_Manfac_scaled'
        exp = download_exposure_from_s3(country, file_short)

    if sector == 'wood':
        file_short = f'manufacturing/manufacturing_sub_exposures/refinement_1/{sector}/country_split/{sector}_NOx_emissions_2011_above_100t_0.1deg_ISO3_values_Manfac_scaled'
        exp = download_exposure_from_s3(country, file_short)

    return exp


def apply_sector_impf_set(hazard, sector, country_iso3alpha):
    haz_type = HAZ_TYPE_LOOKUP[hazard]

    if haz_type == 'TC' and sector == 'agriculture':
        return agriculture.get_impf_set_tc()
    if haz_type == 'TC':
        return ImpactFuncSet([get_sector_impf_tc(country_iso3alpha, sector)])
    if haz_type == 'RF':
        return ImpactFuncSet([get_sector_impf_rf(country_iso3alpha)])
    if haz_type == 'WF':
        return ImpactFuncSet([get_sector_impf_wf(sector)])
    if haz_type == 'WS':
        return stormeurope.get_impf_set(sector)
    if haz_type == 'RC':
        return agriculture.get_impf_set()
    Warning('No impact functions defined for this hazard. Using TC impact functions just so you have something')
    return ImpactFuncSet([get_sector_impf_tc(country_iso3alpha, sector, haz_type)])


def get_sector_impf_tc(country_iso3alpha, sector, haz_type='TC'):
    _, impf_ids, _, region_mapping = ImpfSetTropCyclone.get_countries_per_region()
    region = [region for region, country_list in region_mapping.items() if country_iso3alpha in country_list]
    if len(region) != 1:
        raise ValueError(f'Could not find a unique region for ISO3 code {country_iso3alpha}. Results: {region}')
    region = region[0]
    fun_id = impf_ids[region]
    impf = ImpfSetTropCyclone.from_calibrated_regional_ImpfSet().get_func(haz_type='TC', fun_id=fun_id)
    impf.haz_type = haz_type
    impf.id = 1
    return convert_impf_to_sectoral_bi(impf, sector)


def get_sector_impf_rf(country_iso3alpha, sector):
    # Use the flood module's lookup to get the regional impact function for the country
    country_info = pd.read_csv(RIVER_FLOOD_REGIONS_CSV)
    impf_id = country_info.loc[country_info['ISO'] == country_iso3alpha, 'impf_RF'].values[0]
    # Grab just that impact function from the flood set, and set its ID to 1
    impf_set = flood_imp_func_set()
    impf = impf_set.get_func(haz_type='RF', fun_id=impf_id)
    impf.id = 1
    return convert_impf_to_sectoral_bi(impf, sector)


# for wildfire, not sure if it is working
def get_sector_impf_wf(sector):
    impf = ImpfWildfire.from_default_FIRMS(i_half=409.4) # adpated i_half according to hazard resolution of 4km: i_half=409.4
    impf.haz_type = 'WFseason'  # TODO there is a warning when running the code that the haz_type is set to WFsingle, but if I set it to WFsingle, the code does not work
    return convert_impf_to_sectoral_bi(impf, sector)



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
        country_iso3num = pycountry.countries.get(alpha_3=country_iso3alpha).numeric
        haz = stormeurope.get_hazard(
            scenario=scenario,
            country_iso3alpha=country_iso3alpha
        )
        return haz

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
                year_range="2006_2099",
                scenario=scenario
            )
    else:
        raise ValueError(
            f'Unrecognised haz_type variable: {haz_type}.\nPlease use one of: {list(HAZ_TYPE_LOOKUP.keys())}'
        )
