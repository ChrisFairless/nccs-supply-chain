import os
import traceback
import pandas as pd
import numpy as np
from pathlib import Path
from copy import deepcopy
import json
from datetime import datetime
import typing
import pathos as pa
from functools import partial
import pycountry

from climada.engine import Impact

from pipeline.direct.direct import get_sector_exposure, nccs_direct_impacts_simple
from pipeline.direct.calc_yearset import yearset_from_imp, combine_yearsets
from pipeline.indirect.indirect import dump_direct_to_csv, dump_supchain_to_csv, supply_chain_climada
from utils import folder_naming
from utils.s3client import upload_to_s3_bucket, file_exists_on_s3_bucket, download_from_s3_bucket


DO_PARALLEL = False

DO_DIRECT = True       # Calculate any direct impacts that are missing based on the config
DO_YEARSETS = True     # Calculate any direct impact yearsets that are missing based on the config
DO_MULTIHAZARD = False  # Also combine hazards in each calculation year to shock the supply chain
DO_INDIRECT = True      # Calculate any indirect impacts that are missing based on the config

ncpus = pa.helpers.cpu_count() - 1
ncpus = 3

def run_pipeline_from_config(
        config: dict,
        direct_output_dir: typing.Union[str, os.PathLike] = None,
        indirect_output_dir: typing.Union[str, os.PathLike] = None,
        use_s3: bool = False,
        force_recalculation: bool = False
        ):
    """Run the full model NCCS supply chain from a config dictionary.
    
    The method uses the input config object to create a dataframe with one 
    row for each analysis required for the run, based on the requested 
    scenarios, sectors, countries and hazards. It creates an impact object 
    for each analysis, a yearset based on these impacts, and runs the 
    supply chain model for each yearset, and writes outputs as it goes.

    Parameters
    ----------
    config : dict
        A dictionary describing the full model run configuration. See the 
        examples in run_configurations/ for how these are constructed
    direct_output_dir : str or os.PathLike
        Location to store direct impact calculation results 
        (both impact objects and the yearsets created from them). Generated 
        automatically from the config run name if not provided
    indirect_output_dir : str or os.PathLike
        location to store indirect impact calculation results. 
        Generated automatically from the config run name if not provided
    use_s3 : bool
        Look in the S3 bucket for existing results, and save files to the 
        bucket
    force_recalculation: bool
        If outputs exist for this run name, recalculate them and overwrite.
    """

    if not direct_output_dir:
        direct_output_dir = folder_naming.get_direct_output_dir(config['run_title'])
    
    if not indirect_output_dir:
        indirect_output_dir = folder_naming.get_indirect_output_dir(config['run_title'])

    os.makedirs(direct_output_dir, exist_ok=True)
    os.makedirs(indirect_output_dir, exist_ok=True)

    config['time_run'] = str(datetime.now())
    with open(Path(indirect_output_dir, 'config.json'), 'w') as f:
        json.dump(config, f)
    
    print(f"Direct output will be saved to {direct_output_dir}")
    
    ### --------------------------------- ###
    ### CALCULATE DIRECT ECONOMIC IMPACTS ###
    ### --------------------------------- ###

    ### Read the config to create a list of simulations
    analysis_df = config_to_dataframe(config, direct_output_dir, indirect_output_dir)

    # Generate a dataframe with metadata, and filepaths for each analysis
    # definte in the input config.
    direct_output_dir_impact = Path(direct_output_dir, "impact_raw")
    direct_output_dir_yearsets = Path(direct_output_dir, "yearsets")
    os.makedirs(direct_output_dir_impact, exist_ok=True)
    os.makedirs(direct_output_dir_yearsets, exist_ok=True)

    analysis_df['_direct_impact_already_exists'] = [exists_impact_file(p, use_s3) for p in analysis_df['direct_impact_path']]
    analysis_df['_direct_impact_calculate'] = True if force_recalculation else ~analysis_df['_direct_impact_already_exists']

    def calculate_direct_impacts_from_df(df, use_s3):
        # TODO subset the df before this check is made. Risk of some parallel processes having no work to do
        for _, calc in df.iterrows():            
            if not calc['_direct_impact_calculate']: 
                continue

            try:
                imp = nccs_direct_impacts_simple(
                    haz_type=calc['hazard'],
                    sector=calc['sector'],
                    country=calc['country'],
                    scenario=calc['scenario'],
                    ref_year=calc['ref_year'],
                    business_interruption=config['business_interruption'],
                    calibrated=config['calibrated']
                )
                write_impact_to_file(imp, calc['direct_impact_path'], use_s3)
            except Exception as e:
                print(f"This didn't work: {e}")
    
    if DO_DIRECT:
        if DO_PARALLEL:
            chunk_size = int(np.ceil(analysis_df.shape[0] / ncpus))
            df_chunked = [analysis_df[i:i + chunk_size] for i in range(0, analysis_df.shape[0], chunk_size)]
            calc_partial = partial(calculate_direct_impacts_from_df, use_s3=use_s3)
            with pa.multiprocessing.ProcessPool(ncpus) as pool:
                pool.map(calc_partial, df_chunked)    
        else:
            calculate_direct_impacts_from_df(analysis_df, use_s3)
    else:
        print("Skipping direct impact calculations. Change DO_DIRECT in analysis.py to change this")

    analysis_df['_direct_impact_exists'] = [exists_impact_file(p, use_s3) for p in analysis_df['direct_impact_path']]
    analysis_df.to_csv(Path(direct_output_dir, 'calculations_report.csv'))


    ### ------------------- ###
    ### SAMPLE IMPACT YEARS ###
    ### ------------------- ###

    # Create a yearset for each row of the analysis dataframe
    # This gives us an impact object where each event is a fictional year of events   
    print("Generating yearsets")
    yearset_output_dir = Path(direct_output_dir, "yearsets")
    os.makedirs(yearset_output_dir, exist_ok=True)

    analysis_df['_yearset_already_exists'] = [exists_impact_file(p, use_s3) for p in analysis_df['yearset_path']]
    analysis_df['_yearset_calculate'] = (True if force_recalculation else ~analysis_df['_yearset_already_exists']) * analysis_df['_direct_impact_exists']

    def calculate_yearsets_from_df(df, config, use_s3):
        for _, calc in df.iterrows():
            if not calc['_yearset_calculate']: 
                continue
            try:
                imp_yearset = create_single_yearset(
                    calc,
                    n_sim_years=config['n_sim_years'],
                    seed=config['seed'],
                )
                write_impact_to_file(imp_yearset, calc['yearset_path'], use_s3)
            except Exception as e:
                print(f"This didn't work: {e}") 
    
    if DO_YEARSETS:
        if DO_PARALLEL:
            chunk_size = int(np.ceil(analysis_df.shape[0] / ncpus))
            df_chunked = [analysis_df[i:i + chunk_size] for i in range(0, analysis_df.shape[0], chunk_size)]
            calc_partial = partial(calculate_yearsets_from_df, config=config, use_s3=use_s3)
            with pa.multiprocessing.ProcessPool(ncpus) as pool:
                pool.map(calc_partial, df_chunked)    
        else:
            calculate_yearsets_from_df(analysis_df, config, use_s3)
    else:
        print("Skipping yearset calculations. Change DO_YEARSETS in analysis.py to change this")

    analysis_df['_yearset_exists'] = [exists_impact_file(p, use_s3) for p in analysis_df['yearset_path']]
    analysis_df.to_csv(Path(direct_output_dir, 'calculations_report.csv'))


    # Next: combine yearsets by hazard to create multihazard yearsets

    # We get a bit stricter: each run in the config file should have the same number of scenarios
    _ = _check_config_valid_for_indirect_aggregations(config)
    grouping_cols = ['i_scenario', 'sector', 'country']

    if DO_MULTIHAZARD:
        print("Combining hazards to multihazard yearsets")
        df_aggregated_yearsets = analysis_df \
            .groupby(grouping_cols)[grouping_cols + ['hazard', 'scenario', 'ref_year', 'yearset_path']] \
            .apply(df_create_combined_hazard_yearsets) \
            .reset_index()

        analysis_df = pd.concat([analysis_df, df_aggregated_yearsets]).reset_index()  # That's right! I don't know how to use reset_index!
    else:
        print("Skipping multihazard impact calculations. Change DO_MULTIHAZARD in analysis.py to change this")

    ### ----------------------------------- ###
    ### CALCULATE INDIRECT ECONOMIC IMPACTS ###
    ### ----------------------------------- ###

    # Generate supply chain impacts from the yearsets
    # Create a folder to output the data
    # indirect_output_dir = Path(indirect_output_dir, "results")
    print("Running supply chain calculations")
    os.makedirs(indirect_output_dir, exist_ok=True)
    
    analysis_df['_indirect_exists'] = False  # TODO: update this to check for existing output
    analysis_df['_indirect_calculate'] = analysis_df['_yearset_exists']

    def calculate_indirect_impacts_from_df(df, io_a, config, direct_output_dir):
        # TODO consider some sort of grouping so that we don't need to load sector exposures each time...
        # No need to parallelise this: it already seems to max out the CPUs
        for i, row in df.iterrows():
            print("SUPPLY CHAIN ROW")
            print(row.to_dict())

            if not row['_indirect_calculate']:
                print('No yearset data available. Skipping supply chain calculation')
                continue

            # TODO put this in a function: it's used in the supply_chain_climada method too
            country_iso3alpha = pycountry.countries.get(name=row['country']).alpha_3
            direct_path = f"{direct_output_dir}/" \
                f"direct_impacts" \
                f"_{row['hazard']}" \
                f"_{row['sector'].replace(' ', '_')[:15]}" \
                f"_{row['scenario']}" \
                f"_{row['ref_year']}" \
                f"_{country_iso3alpha}" \
                f".csv"

            if os.path.exists(direct_path):
                print(f'Output already exists, skipping calculation: {direct_path}')
                continue

            try:
                print(f"Calculating indirect impacts for {row['country']} {row['sector']}...")
                imp = Impact.from_hdf5(row['yearset_path'])
                if not imp.at_event.any():
                    # TODO return an object with zero losses so that there's data
                    print("No non-zero impacts. Skipping")
                    continue
                supchain = supply_chain_climada(
                    get_sector_exposure(sector=row['sector'], country=row['country']),
                    imp,
                    impacted_sector=row['sector'],
                    io_approach=io_a
                )
                # save direct impacts to a csv
                # TODO: also save to S3
                dump_direct_to_csv(
                    supchain=supchain,
                    haz_type=row['hazard'],
                    sector=row['sector'],
                    scenario=row['scenario'],
                    ref_year=row['ref_year'],
                    country=row['country'],
                    n_sim=config['n_sim_years'],
                    return_period=100,
                    output_dir=direct_output_dir
                )
                # save indirect impacts to a csv
                # TODO: also save to S3
                dump_supchain_to_csv(
                    supchain=supchain,
                    haz_type=row['hazard'],
                    sector=row['sector'],
                    scenario=row['scenario'],
                    ref_year=row['ref_year'],
                    country=row['country'],
                    n_sim=config['n_sim_years'],
                    return_period=100,
                    io_approach=io_a,
                    output_dir=indirect_output_dir
                )
                df.loc[i, '_indirect_exists'] = True

            except Exception as e:
                print(f"Error calculating indirect impacts for {row['country']} {row['sector']}:")
                print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
                print(e)

    # Run the Supply Chain for each country and sector and output the data needed to csv
    if DO_INDIRECT:
        for io_a in config['io_approach']:
            # For now we're not parallelising this: looks like there's not much time gained. But should time it properly.
            calculate_indirect_impacts_from_df(analysis_df, io_a, config, direct_output_dir)
    else:
        print("Skipping supply chain calculations. Change DO_INDIRECT in analysis.py to change this")

    analysis_df.to_csv(Path(indirect_output_dir, 'calculations_report.csv'))

    print("Done!\nTo show the Dashboard run:\nbokeh serve dashboard.py --show")
    print("Don't forget to update the current run title within the dashboard.py script: RUN_TITLE")


def config_to_dataframe(
        config: dict,
        direct_output_dir: typing.Union[str, os.PathLike],
        indirect_output_dir: typing.Union[str, os.PathLike]):
    """Convert a run config to a dataframe of required model runs. 
    Note: these don't include model runs that combine hazards, sectors and 
    countries, which are created after this first set is run.

    Parameters
    ----------
    config : dict
        A config object. See run_configurations/ for the format
    direct_output_dir : str or os.PathLike
        Location to save direct impact modelling outputs
    indirect_output_dir : str or os.PathLike
        Location to save supply chain impact modelling outputs
        
    Returns
    -------
    pandas.DataFrame
        A dataframe with one row for each simulation that will be run in the 
        supply chain modelling, and the parameters required to run the 
        simulations.
    """
    df = pd.DataFrame([
        {
                'hazard': run['hazard'],
                'sector': sector,
                'country': country,
                'scenario': scenario['scenario'],
                'i_scenario': i,
                'ref_year': scenario['ref_year'],
        }
        for run in config['runs']
        for i, scenario in enumerate(run['scenario_years'])
        for country in run['countries']
        for sector in run['sectors']
    ])
    for i, row in df.iterrows():
        direct_impact_filename = folder_naming.get_direct_namestring(
            prefix="impact_raw",
            extension="hdf5",
            haz_type=row['hazard'],
            sector=row['sector'],
            country_iso3alpha=row['country'],
            scenario=row['scenario'],
            ref_year=row['ref_year']
        )
        direct_impact_path = Path(direct_output_dir, "impact_raw", direct_impact_filename)
        df.loc[i, 'direct_impact_path'] = direct_impact_path

        yearset_filename = folder_naming.get_direct_namestring(
            prefix='yearset',
            extension='hdf5',
            haz_type=row['hazard'],
            sector=row['sector'],
            scenario=row['scenario'],
            ref_year=row['ref_year'],
            country_iso3alpha=row['country']
        )
        yearset_path = Path(direct_output_dir, "yearsets", yearset_filename)
        df.loc[i, 'yearset_path'] = yearset_path

    return df


def create_single_yearset(
        analysis_spec: pd.DataFrame,
        n_sim_years: int,
        seed: int,
        ):
    """Take the metadata for an analysis and create an impact yearset if it 
    doesn't already exist. These are created as files and a `yearset_path` added
    to the input dataframe. 

    Parameters
    ----------
    analysis_spec : pd.Series
        A row of a dataframe created by config_to_dataframe
    n_sim_years : int
        Number of years to create for each output yearset
    seed : int
        The random number seed to use in each yearset's sampling
    """

    row = analysis_spec.copy().to_dict()

    print(f'Generating yearsets for {row["yearset_path"]}')
    imp = get_impact_from_file(row['direct_impact_path'])

    # TODO we don't actually want to generate a yearset if we're looking at observed events
    imp_yearset = yearset_from_imp(
        imp,
        n_sim_years,
        cap_exposure=get_sector_exposure(row['sector'], row['country']),
        seed=seed
    )
    # TODO drop the impact matrix to save RAM/HD space once SupplyChain is updated and doesn't need it

    return imp_yearset


def df_create_combined_hazard_yearsets(
        df: pd.DataFrame
    ):
    """For each grouping of scenario, country and sector, combine hazard yearsets 

    Parameters
    ----------
    df : pandas.DataFrame
        Dataframe containing analyses metadata created by config_to_dataframe

    Returns
    -------
    pandas.DataFrame
        A dataframe containing analysis metadata for a supply chain analysis 
        for all hazards combined.

    Notes
    -----
    This function adapts pymrio.tools.iomath.calc_x to compute
    value added (v).
    """
    
    r = df.iloc[0].to_dict()
    yearset_output_dir = os.path.dirname(r['yearset_path'])
    print(r)
    combined_filename = folder_naming.get_direct_namestring(
            prefix='yearset',
            extension='hdf5',
            haz_type='COMBINED', sector=r['sector'], scenario=r['scenario'], ref_year=r['ref_year'], country_iso3alpha=r['country'])
    combined_path = Path(yearset_output_dir, combined_filename)

    impact_list = [get_impact_from_file(f) for f in df['yearset_path'] if os.path.exists(f)]

    out = {
        'hazard': 'COMBINED',
        'scenario': r['scenario'], 
        'ref_year': r['ref_year'],
    }

    if len(impact_list) > 0:
        combined = combine_yearsets(
            impact_list = impact_list,
            cap_exposure = get_sector_exposure(r['sector'], r['country'])
        )
        # TODO drop the impact matrix to save RAM/HD space once SupplyChain is updated and doesn't need it

        combined.write_hdf5(combined_path)
        out['yearset_path'] = combined_path
        out['_yearset_exists'] = True
        # out['annual_impacts'] = combined.at_event
    else:
        out['_yearset_exists'] = False

    return pd.Series(out)



def exists_impact_file(filepath: str, use_s3: bool = False):
    """Check if an impact object exists at a filepath, checking the corresponding 
    location on the S3 bucket if requested if the file is not present locally.

    Parameters
    ----------
    filepath : str
        Path to requested file
    use_s3 : bool
        If True, check for a file with this name on the s3 bucket as well 

    Returns
    -------
    bool
        Whether the impact file exists
    """
    if os.path.exists(filepath):
        return True
    if use_s3:
        filename = os.path.basename(filepath)
        return file_exists_on_s3_bucket(filepath)
    return False


def get_impact_from_file(filepath: str, use_s3: bool = False):
    """Load an impact object from a filepath, checking the corresponding 
    location on the S3 bucket if requested if the file is not present locally.

    Parameters
    ----------
    filepath : str
        Path to requested file
    use_s3 : bool
        If True, check for a file with this name on the s3 bucket as well 

    Returns
    -------
    climada.engine.impact.Impact
        CLIMADA Impact object loaded from the filepath
    """
    if os.path.exists(filepath):
        return Impact.from_hdf5(filepath)
    if use_s3:
        filename = os.path.basename(filepath)
        download_from_s3_bucket(s3_filename=filename, output_path=filepath)
        return Impact.from_hdf5(filepath)
    raise FileExistsError(f"Could not find an impact object at {filepath}")


def write_impact_to_file(imp, filepath: str, use_s3: bool = False):
    imp.write_hdf5(filepath)
    if use_s3:
        filename = os.path.basename(filepath)
        upload_to_s3_bucket(filename)  


def _check_config_valid_for_indirect_aggregations(config):
    # Check all scenarios lists are the same length OR length 1
    scenarios_list_list = [run['scenario_years'] for run in config['runs']]
    n_scenarios_list = [len(scenario_list) for scenario_list in scenarios_list_list if len(scenario_list) > 1]
    if len(np.unique(n_scenarios_list)) > 1:
        raise ValueError('To continue with generation of yearsets and indirect impacts, the config needs to have the '\
                         'same number of scenarios specified for each hazard in the config, or just one scenario.')
    return 1 if len(n_scenarios_list) == 0 else n_scenarios_list[0]


if __name__ == "__main__":
    # This is the full run
    # from run_configurations.config import CONFIG

    # This is for testing
    from run_configurations.test_config import CONFIG  # change here to test_config if needed

    run_pipeline_from_config(CONFIG)
