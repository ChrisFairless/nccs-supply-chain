import sys
import pandas as pd
import traceback
from pathlib import Path
import pycountry
from climada.engine import Impact

sys.path.append('../')   # HELP: what's the correct way to load things from the parent directory?
from analysis import config_to_dataframe, df_extend_with_multihazard, get_impact_from_file, DO_MULTIHAZARD
from pipeline.direct.direct import get_hazard, get_sector_exposure
from utils import folder_naming

use_s3 = False  # Not ready yet

# Validate all the data!

def validate_from_config(config):
    direct_output_dir = folder_naming.get_direct_output_dir(config['run_title'])
    direct_output_dir_impact = Path(direct_output_dir, "impact_raw")
    direct_output_dir_yearsets = Path(direct_output_dir, "yearsets")
    indirect_output_dir = folder_naming.get_indirect_output_dir(config['run_title'])

    analysis_df = config_to_dataframe(config, direct_output_dir, indirect_output_dir)

    # HAZARD
    haz_id_cols = ['hazard', 'country', 'scenario', 'i_scenario', 'ref_year']
    hazard_df = analysis_df[haz_id_cols].drop_duplicates()
    haz_results = []
    for _, row in hazard_df.iterrows():
        country_iso3alpha = pycountry.countries.get(name=row['country']).alpha_3
        d = {
            'hazard': row['hazard'],
            'country': row['country'],
            'scenario': row['scenario'],
            'i_scenario': row['i_scenario'],
            'ref_year': row['ref_year'],
            'haz_exists': False,
            'haz_exists_error': None,
            'haz_has_events': None,
            'haz_nonzero': None
        }
        try:
            haz = get_hazard(row['hazard'], country_iso3alpha, row['scenario'], row['ref_year'])
            d['haz_exists'] = True
            d['haz_has_events'] = haz.intensity.shape[0] > 0
            d['haz_nonzero'] = ~(haz.intensity.max() == 0 and haz.intensity.min() == 0)
        except Exception as e:
            d['haz_exists_error'] = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        haz_results.append(d)
    haz_results = pd.DataFrame(haz_results)
    analysis_df = analysis_df.merge(haz_results, how='left', on=haz_id_cols)


    # EXPOSURE
    exposure_id_cols = ['sector', 'country']
    exposure_df = analysis_df[exposure_id_cols].drop_duplicates()
    exp_results = []
    for _, row in exposure_df.iterrows():
        country_iso3alpha = pycountry.countries.get(name=row['country']).alpha_3
        d = {
            'sector': row['sector'],
            'country': row['country'],
            'exp_exists': False,
            'exp_exists_error': None,
            'exp_has_events': None,
            'exp_nonzero': None
        }
        try:
            exp = get_sector_exposure(row['sector'], country_iso3alpha)
            d['exp_exists'] = True
            d['exp_has_values'] = exp.gdf.shape[0] > 0
            d['exp_nonzero'] = exp.gdf.value.max() != 0
        except Exception as e:
            d['exp_exists_error'] = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        exp_results.append(d)
    exp_results = pd.DataFrame(exp_results)
    analysis_df = analysis_df.merge(exp_results, how='left', on=exposure_id_cols)

    # DIRECT IMPACTS
    impact_id_cols = ['hazard', 'sector', 'country', 'scenario', 'i_scenario', 'ref_year']
    imp_results = []
    for _, row in analysis_df.iterrows():
        country_iso3alpha = pycountry.countries.get(name=row['country']).alpha_3
        d = {
            'hazard': row['hazard'],
            'sector': row['sector'],
            'country': row['country'],
            'scenario': row['scenario'],
            'i_scenario': row['i_scenario'],
            'ref_year': row['ref_year'],
            'imp_exists': False,
            'imp_exists_error': None,
            'imp_has_events': None,
            'imp_nonzero': None
        }
        try:
            imp = get_impact_from_file(row['direct_impact_path'], use_s3=use_s3)
            d['imp_exists'] = True
            d['imp_has_events'] = len(imp.at_event) > 0
            d['imp_nonzero'] = ~(imp.at_event.max() == 0 and imp.at_event.min() == 0)
        except Exception as e:
            d['imp_exists_error'] = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        imp_results.append(d)
    imp_results = pd.DataFrame(imp_results)
    analysis_df = analysis_df.merge(imp_results, how='left', on=impact_id_cols)


    # YEARSETS
    yearset_results = []
    for _, row in analysis_df.iterrows():
        country_iso3alpha = pycountry.countries.get(name=row['country']).alpha_3
        d = {
            'hazard': row['hazard'],
            'sector': row['sector'],
            'country': row['country'],
            'scenario': row['scenario'],
            'i_scenario': row['i_scenario'],
            'ref_year': row['ref_year'],
            'yearset_exists': False,
            'yearset_exists_error': None,
            'yearset_has_events': None,
            'yearset_nonzero': None
        }
        try:
            yearset = get_impact_from_file(row['yearset_path'], use_s3=use_s3)
            d['yearset_exists'] = True
            d['yearset_has_events'] = len(yearset.at_event) > 0
            d['yearset_nonzero'] = ~(yearset.at_event.max() == 0 and yearset.at_event.min() == 0)
        except Exception as e:
            d['yearset_exists_error'] = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        yearset_results.append(d)
    yearset_results = pd.DataFrame(yearset_results)
    analysis_df = analysis_df.merge(yearset_results, how='left', on=impact_id_cols)


    # SUPPLY CHAIN DIRECT IMPACTS
    supchain_direct_results = []
    for _, row in analysis_df.iterrows():
        country_iso3alpha = pycountry.countries.get(name=row['country']).alpha_3
        d = {
            'hazard': row['hazard'],
            'sector': row['sector'],
            'country': row['country'],
            'scenario': row['scenario'],
            'i_scenario': row['i_scenario'],
            'ref_year': row['ref_year'],
            'supchain_direct_exists': False,
            'supchain_direct_exists_error': None,
            'supchain_direct_nonzero': None
        }
        try:
            supchain_direct = pd.read_csv(row['supchain_direct_path'])
            d['supchain_direct_exists'] = True
            d['supchain_direct_nonzero'] = supchain_direct.shape[0] > 0 and supchain_direct['AAPL'].max() > 0
        except Exception as e:
            d['supchain_direct_exists_error'] = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        supchain_direct_results.append(d)
    supchain_direct_results = pd.DataFrame(supchain_direct_results)
    analysis_df = analysis_df.merge(supchain_direct_results, how='left', on=impact_id_cols)

    # SUPPLY CHAIN INDIRECT IMPACTS: LEONTIEF
    supchain_indirect_leontief_results = []
    for _, row in analysis_df.iterrows():
        country_iso3alpha = pycountry.countries.get(name=row['country']).alpha_3
        d = {
            'hazard': row['hazard'],
            'sector': row['sector'],
            'country': row['country'],
            'scenario': row['scenario'],
            'i_scenario': row['i_scenario'],
            'ref_year': row['ref_year'],
            'supchain_indirect_leontief_exists': False,
            'supchain_indirect_leontief_exists_error': None,
            'supchain_indirect_leontief_nonzero': None
        }
        try:
            supchain_indirect_leontief = pd.read_csv(row['supchain_indirect_leontief_path'])
            d['supchain_direct_leontief_exists'] = True
            d['supchain_direct_leontief_nonzero'] = supchain_indirect_leontief.shape[0] > 0 and supchain_indirect_leontief['AAPL'].max() > 0
        except Exception as e:
            d['supchain_indirect_leontief_exists_error'] = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        supchain_indirect_leontief_results.append(d)
    supchain_indirect_leontief_results = pd.DataFrame(supchain_indirect_leontief_results)
    analysis_df = analysis_df.merge(supchain_indirect_leontief_results, how='left', on=impact_id_cols)

    # SUPPLY CHAIN INDIRECT IMPACTS: GHOSH
    supchain_indirect_ghosh_results = []
    for _, row in analysis_df.iterrows():
        d = {
            'hazard': row['hazard'],
            'sector': row['sector'],
            'country': row['country'],
            'scenario': row['scenario'],
            'i_scenario': row['i_scenario'],
            'ref_year': row['ref_year'],
            'supchain_indirect_ghosh_exists': False,
            'supchain_indirect_ghosh_exists_error': None,
            'supchain_indirect_ghosh_nonzero': None
        }
        try:
            supchain_indirect_ghosh = pd.read_csv(row['supchain_indirect_ghosh_path'])
            d['supchain_direct_ghosh_exists'] = True
            d['supchain_direct_ghosh_nonzero'] = supchain_indirect_ghosh.shape[0] > 0 and supchain_indirect_ghosh['iAAPL'].max() > 0
        except Exception as e:
            d['supchain_indirect_ghosh_exists_error'] = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        supchain_indirect_ghosh_results.append(d)
    supchain_indirect_ghosh_results = pd.DataFrame(supchain_indirect_ghosh_results)
    analysis_df = analysis_df.merge(supchain_indirect_ghosh_results, how='left', on=impact_id_cols)

    out_path = Path(folder_naming.get_run_dir(config['run_title']), 'validation.csv')
    analysis_df.to_csv(out_path)

    print('DATA VALIDATION SUMMARY:')
    print('========================')
    print(f'Run name:                 {config["run_title"]}')
    print(f'Hazard calculations:      {[run["hazard"] for run in config["runs"]]}')
    print(f'Hazard data exists:       {haz_results["haz_exists"].sum()} / {haz_results.shape[0]}')
    print(f'Exposure data exists:     {exp_results["exp_exists"].sum()} / {exp_results.shape[0]}')
    print(f'Impact data exists:       {imp_results["imp_exists"].sum()} / {imp_results.shape[0]}')
    print(f'Yearset data exists:      {yearset_results["yearset_exists"].sum()} / {yearset_results.shape[0]}')
    print(f'Supchain direct exists:   {supchain_direct_results["supchain_direct_exists"].sum()} / {supchain_direct_results.shape[0]}')
    print(f'Supchain leontief exists: {supchain_indirect_leontief_results["supchain_indirect_leontief_exists"].sum()} / {supchain_indirect_leontief_results.shape[0]}')
    print(f'Supchain ghosh exists:    {supchain_indirect_ghosh_results["supchain_indirect_ghosh_exists"].sum()} / {supchain_indirect_ghosh_results.shape[0]}')
    print('')
    print(f'More details and diagnostics in {out_path}')


if __name__ == "__main__":
    from run_configurations.config_temp_intermediate_finishing import CONFIG  # change here to test_config if needed
    # from run_configurations.test.test_config import CONFIG  # change here to test_config if needed
    validate_from_config(CONFIG)