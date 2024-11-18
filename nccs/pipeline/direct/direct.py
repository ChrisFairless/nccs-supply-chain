# for the wilfire impact function:
# /climada_petals/blob/main/climada_petals/entity/impact_funcs/wildfire.py

from pathlib import Path

import pandas as pd
import pycountry
from climada.engine.impact_calc import ImpactCalc
from climada.entity import Exposures
from climada.entity import ImpactFuncSet, ImpfSetTropCyclone, ImpfTropCyclone
from climada.entity.impact_funcs.storm_europe import ImpfStormEurope
from climada.hazard import Hazard
from climada.util.api_client import Client
from climada_petals.entity.impact_funcs.river_flood import RIVER_FLOOD_REGIONS_CSV, flood_imp_func_set
# for the wilfire impact function:
# https://github.com/CLIMADA-project/climada_petals/blob/main/climada_petals/entity/impact_funcs
from climada_petals.entity.impact_funcs.wildfire import ImpfWildfire

from exposures.utils import root_dir
from nccs.pipeline.direct import agriculture, stormeurope
from nccs.pipeline.direct.business_interruption import convert_impf_to_sectoral_bi_dry
from nccs.pipeline.direct.business_interruption import convert_impf_to_sectoral_bi_wet
from nccs.utils.folder_naming import get_resources_dir
from nccs.utils.s3client import download_from_s3_bucket

project_root = root_dir()
# /wildfire.py

HAZ_TYPE_LOOKUP = {
    'tropical_cyclone',
    'river_flood',
    'wildfire',
    'storm_europe',
    "relative_crop_yield",
}


def nccs_direct_impacts_simple(
        haz_type,
        sector,
        country,
        scenario,
        ref_year,
        business_interruption=True,
        calibrated=True):
    # Country names can be checked here: https://github.com/flyingcircusio/pycountry/blob/main/src/pycountry
    # /databases/iso3166-1.json
    country_iso3alpha = pycountry.countries.get(name=country).alpha_3
    haz = get_hazard(haz_type, country_iso3alpha, scenario, ref_year)
    exp = get_sector_exposure(sector, country)  # was originally here
    # exp = sectorial_exp_CI_MRIOT(country=country_iso3alpha, sector=sector) #replaces the command above
    impf_set = apply_sector_impf_set(haz_type, sector, country_iso3alpha, business_interruption, calibrated)
    imp = ImpactCalc(exp, impf_set, haz).impact(save_mat=True)
    imp.event_name = [str(e) for e in imp.event_name]
    # Drop events with no impact to save space
    # imp = imp.select(event_ids = [id for id, event_impact in zip(imp.event_id, imp.at_event) if event_impact > 0])
    return imp


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


def download_exposure_from_s3(country, file_short):
    country_iso3alpha = pycountry.countries.get(name=country).alpha_3
    s3_filepath = f'exposures/{file_short}_{country_iso3alpha}.h5'
    outputfile = f'{project_root}/exposures/{file_short}_{country_iso3alpha}.h5'
    download_from_s3_bucket(s3_filepath, outputfile)
    h5_file = pd.read_hdf(outputfile)
    # Generate an Exposures instance from DataFrame
    exp = Exposures(h5_file)
    exp.set_geometry_points()
    exp.gdf['value'] = exp.gdf.value
    exp.check()
    return exp


def download_hazard_from_s3(s3_filepath):
    outputfile = f'{project_root}/resources/{s3_filepath}'
    download_from_s3_bucket(s3_filepath, outputfile)
    haz = Hazard.from_hdf5(outputfile)
    haz.check()
    return haz


def get_sector_exposure(sector, country):
    """
    There are now commeneted versions that worked previously only locally, as the files were not synched. The best
    guesstimate
    results are now also availabe in the s3 bucket and could be selected by changing the file path to the s3 bucket
    would require to create a new donwload function, as for instance the mining file is an xlsx and would not work
    with the opening command
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

        # current active version
        file_short = (f'manufacturing/manufacturing_general_exposure/refinement_1/country_split'
                      f'/global_noxemissions_2011_above_100t_0.1deg_ISO3_values_Manfac_scaled')
        exp = download_exposure_from_s3(country, file_short)

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

        file_short = (f'{ sector}/refinement_1/country_split/'
                      f'global_miningarea_v2_30arcsecond_converted_ISO3_improved_values_MP_scaled')
        exp = download_exposure_from_s3(country, file_short)

        # only used for best guesstimate
    # if sector == 'electricity':
    #     # load an exposure from an excel file
    #     input_file = f'{get_resource_dir()}/utilities/best_guesstimate/utilities_power_plant_global_database_WRI.xlsx'
    #     excel_data = pd.read_excel(input_file)
    #     # Generate an Exposures instance from DataFrame
    #     exp = Exposures(excel_data)
    #     exp.set_geometry_points()
    #     exp.gdf['value'] = exp.gdf.value
    #     exp.check()

    # In this case a sub sector of agriculture is selected, this is only applied during the direct impacts
    if sector.startswith('agriculture_'):
        _, crop_type = agriculture.split_agriculture_sector(sector)
        exp = agriculture.get_exposure(crop_type=crop_type, scenario="histsoc", irr="firr")

    if sector == "agriculture":
        # For agriculture, we need to combine the exposures for the different crop types. Since we
        # have already merged the yearsets for the different crop types.
        exps = [agriculture.get_exposure(crop_type=crop_type, scenario="histsoc", irr="firr")
                for crop_type in ["whe", "mai", "soy", "ric"]]
        # Sum up the exposures
        exp = exps[0].copy()
        columns_to_sum = ["impf_RC",  "impf_",  "value"]
        for i in range(1, len(exps)):
            exp.gdf[columns_to_sum] += exps[i].gdf[columns_to_sum]

    if sector == 'forestry':
        # exp = load_forestry_exposure() #only used for best guesstimate
        file_short = f'forestry/refinement_1/country_split/{sector}_values_MRIO_avg(WB-v2)'
        exp = download_exposure_from_s3(country, file_short)

    # Utilities
    if sector == 'energy':
        file_short = f'utilities/refinement_1/Subscore_{sector}/country_split/Subscore_{sector}_MRIO'
        exp = download_exposure_from_s3(country, file_short)

    if sector == 'waste':
        file_short = f'utilities/refinement_1/Subscore_{sector}/country_split/Subscore_{sector}_MRIO'
        exp = download_exposure_from_s3(country, file_short)

    if sector == 'water':
        file_short = f'utilities/refinement_1/Subscore_{sector}/country_split/Subscore_{sector}_MRIO'
        exp = download_exposure_from_s3(country, file_short)

    # raw materials
    if sector == 'pharmaceutical':
        file_short = (f'manufacturing/manufacturing_sub_exposures/refinement_1/{sector}/country_split/'
                      f'{sector}_NMVOC_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled')
        exp = download_exposure_from_s3(country, file_short)

    if sector == 'basic_metals':
        file_short = (f'manufacturing/manufacturing_sub_exposures/refinement_1/{sector}/country_split'
                      f'/{sector}_CO_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled')
        exp = download_exposure_from_s3(country, file_short)

    if sector == 'chemical':
        file_short = (f'manufacturing/manufacturing_sub_exposures/refinement_1/{sector}_process/country_split/'
                      f'{sector}_process_NMVOC_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled')
        exp = download_exposure_from_s3(country, file_short)

    if sector == 'food':
        file_short = (f'manufacturing/manufacturing_sub_exposures/refinement_1/{sector}_and_paper/country_split'
                      f'/{sector}_and_paper_NOX_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled')
        exp = download_exposure_from_s3(country, file_short)

    if sector == 'non_metallic_mineral':
        file_short = (f'manufacturing/manufacturing_sub_exposures/refinement_1/{sector}/country_split/'
                      f'{sector}_PM10_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled')
        exp = download_exposure_from_s3(country, file_short)

    if sector == 'refin_and_transform':
        file_short = (f'manufacturing/manufacturing_sub_exposures/refinement_1/{sector}/country_split/'
                      f'{sector}_NOx_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled')
        exp = download_exposure_from_s3(country, file_short)

    if sector == 'rubber_and_plastic':
        file_short = (f'manufacturing/manufacturing_sub_exposures/refinement_1/{sector}/country_split/'
                      f'{sector}_NOx_emissions_2011_above_100t_0.1deg_ISO3_values_Manfac_scaled')
        exp = download_exposure_from_s3(country, file_short)

    if sector == 'wood':
        file_short = (f'manufacturing/manufacturing_sub_exposures/refinement_1/{sector}/country_split'
                      f'/{sector}_NOx_emissions_2011_above_100t_0.1deg_ISO3_values_Manfac_scaled')
        exp = download_exposure_from_s3(country, file_short)

    if sector == 'economic_assets':
        client = Client()
        exp = client.get_litpop(country)

    exp.gdf.reset_index(inplace=True)

    return exp


def apply_sector_impf_set(hazard, sector, country_iso3alpha, business_interruption=True, calibrated=True):
    # haz_type = HAZ_TYPE_LOOKUP[hazard]

    if not business_interruption or sector in ['agriculture', 'economic_assets']:
        sector_bi = None
    else:
        sector_bi = sector

    if hazard == 'tropical_cyclone' and sector == 'agriculture':
        return agriculture.get_impf_set_tc()
    if hazard == 'tropical_cyclone':
        return ImpactFuncSet([get_sector_impf_tc(country_iso3alpha, sector_bi, calibrated)])
    if hazard == 'river_flood':
        return ImpactFuncSet([get_sector_impf_rf(country_iso3alpha, sector_bi)])
    if hazard == 'wildfire':
        return ImpactFuncSet([get_sector_impf_wf(sector_bi)])
    if hazard == 'storm_europe':
        return ImpactFuncSet([get_sector_impf_stormeurope(sector_bi)])
    if hazard.startswith('relative_crop_yield'):
        _, crop_type = agriculture.split_agriculture_hazard(hazard)
        return agriculture.get_impf_set(crop_type)
    raise ValueError(f'No impact functions defined for hazard {hazard}')


def get_sector_impf_tc(country_iso3alpha, sector_bi, calibrated=True):
    _, impf_ids, _, region_mapping = ImpfSetTropCyclone.get_countries_per_region()
    region = [region for region, country_list in region_mapping.items() if country_iso3alpha in country_list]
    if len(region) != 1:
        raise ValueError(f'Could not find a unique region for ISO3 code {country_iso3alpha}. Results: {region}')
    region = region[0]

    if calibrated:
        calibrated_impf_parameters_file = Path(
            get_resources_dir(),
            'impact_functions',
            'tropical_cyclone',
            'calibrated_emanuel_v1.csv'
        )
        calibrated_impf_parameters = pd.read_csv(calibrated_impf_parameters_file).set_index(['region'])
        impf = ImpfTropCyclone.from_emanuel_usa(
            scale=calibrated_impf_parameters.loc[region, 'scale'],
            v_thresh=calibrated_impf_parameters.loc[region, 'v_thresh'],
            v_half=calibrated_impf_parameters.loc[region, 'v_half']
        )
    else:
        fun_id = impf_ids[region]
        impf = ImpfSetTropCyclone.from_calibrated_regional_ImpfSet().get_func(
            haz_type='TC',
            fun_id=fun_id
        )  # To use Eberenz functions

    impf.id = 1
    if not sector_bi:
        return impf
    return convert_impf_to_sectoral_bi_dry(impf, sector_bi)


#####
## Option 2, apply BI scaling but keep global emanuel function
#####
# def get_sector_impf_tc(country_iso3alpha, sector_bi):
#     # TODO: load regional impfs based on country and
#     haz_type = 'TC'
#     impf = ImpfTropCyclone.from_emanuel_usa()
#     impf.haz_type = haz_type
#     if not sector_bi:
#         return impf
#     return convert_impf_to_sectoral_bi_dry(impf, sector_bi)


def get_sector_impf_rf(country_iso3alpha, sector_bi):
    # Use the flood module's lookup to get the regional impact function for the country
    country_info = pd.read_csv(RIVER_FLOOD_REGIONS_CSV)
    impf_id = country_info.loc[country_info['ISO'] == country_iso3alpha, 'impf_RF'].values[0]
    # Grab just that impact function from the flood set, and set its ID to 1
    impf_set = flood_imp_func_set()
    impf_set.plot()
    impf_AFR = impf_set.get_func(fun_id=1)
    impf_AFR[0].plot()

    impf_ASIA = impf_set.get_func(fun_id=2)
    impf_ASIA[0].plot()

    impf_EU = impf_set.get_func(fun_id=3)
    impf_EU[0].plot()

    impf_NA = impf_set.get_func(fun_id=4)
    impf_NA[0].plot()

    impf_OCE = impf_set.get_func(fun_id=5)
    impf_OCE[0].plot()

    impf_SAM = impf_set.get_func(fun_id=6)
    impf_SAM[0].plot()

    impf = impf_set.get_func(haz_type='RF', fun_id=impf_id)
    impf.id = 1
    if not sector_bi:
        return impf
    return convert_impf_to_sectoral_bi_wet(impf, sector_bi)


def get_sector_impf_stormeurope(sector_bi):
    impf = ImpfStormEurope.from_schwierz()
    if not sector_bi:
        return impf
    return convert_impf_to_sectoral_bi_dry(impf, sector_bi)


# for wildfire, not sure if it is working
def get_sector_impf_wf(sector_bi):
    impf = ImpfWildfire.from_default_FIRMS(
        i_half=409.4
    )  # adpated i_half according to hazard resolution of 4km: i_half=409.4
    impf.haz_type = 'WFseason'  # TODO there is a warning when running the code that the haz_type is set to WFsingle,
    # but if I set it to WFsingle, the code does not work
    if not sector_bi:
        return impf
    return convert_impf_to_sectoral_bi_dry(impf, sector_bi)


def get_hazard(haz_type, country_iso3alpha, scenario, ref_year):
    client = Client()
    if haz_type == 'tropical_cyclone':
        if scenario == 'None' and ref_year == 'historical':
            s3_path = f'hazard/tc_wind/historical/tropcyc_{country_iso3alpha}_historical.hdf5'
        else:
            s3_path = (f'hazard/tc_wind/{scenario}_{ref_year}/tropcyc_150arcsec_25synth_'
                       f'{country_iso3alpha}_1980_to_2023_{scenario}_{ref_year}.hdf5')
        return download_hazard_from_s3(s3_path)

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

    elif haz_type.startswith("relative_crop_yield"):
        _, crop_type = agriculture.split_agriculture_hazard(haz_type)
        # TODO currently always returns the same hazard
        if scenario == 'None' and ref_year == "historical":
            # For soy, there is another historical period available (due to availability)
            if crop_type == 'soy':
                return agriculture.get_hazard(
                    country=country_iso3alpha,
                    year_range="1980_2012",
                    scenario="historical",
                    crop_type=crop_type
                )
            # For the other crop types we use this historical period (due to availability)
            else:
                return agriculture.get_hazard(
                    country=country_iso3alpha,
                    year_range="1971_2001",
                    scenario="historical",
                    crop_type=crop_type
                )
        else:
            return agriculture.get_hazard(
                country=country_iso3alpha,
                year_range="2006_2099",
                scenario=scenario,
                crop_type=crop_type
            ).select(date=('2045-01-01', '2074-12-31'))
    else:
        raise ValueError(
            f'Unrecognised haz_type variable: {haz_type}.\nPlease use one of: {list(HAZ_TYPE_LOOKUP)}'
        )
