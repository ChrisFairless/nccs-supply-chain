import json
import logging
import os
import sys
import typing
import warnings
from datetime import datetime
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd
import pathos as pa
import pycountry
from climada.engine import Impact
from climada.util.config import CONFIG as CLIMADA_CONFIG

from nccs.pipeline.direct.calc_yearset import combine_yearsets, yearset_from_imp
from nccs.pipeline.direct.direct import get_sector_exposure, nccs_direct_impacts_simple
from nccs.pipeline.indirect.indirect import dump_direct_to_csv, dump_supchain_to_csv, supply_chain_climada
from nccs.utils import folder_naming
from nccs.utils.s3client import download_from_s3_bucket, file_exists_on_s3_bucket, upload_to_s3_bucket

LOGGER = logging.getLogger(__name__)


def run_pipeline_from_config(
        config: dict,
        direct_output_dir: typing.Union[str, os.PathLike] = None,
        indirect_output_dir: typing.Union[str, os.PathLike] = None,
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
    """

    LOGGER.setLevel(config['log_level'])
    FORMATTER = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    CONSOLE = logging.StreamHandler(stream=sys.stdout)
    CONSOLE.setFormatter(FORMATTER)
    LOGGER.addHandler(CONSOLE)
    # Note: the logging level for CLIMADA is set separately in the climada.conf file

    if config['log_level'] != CLIMADA_CONFIG.log_level:
        LOGGER.info(
            f'To change the logging level of CLIMADA, edit climada.conf in the root directory and set log_level to '
            f'INFO or DEBUG.' \
            f'Current level is {CLIMADA_CONFIG.log_level}'
        )

    if config['log_level'] != "DEBUG":
        # CLIMADA is full of deprecation warnings that make it hard to follow the output 
        warnings.filterwarnings("ignore", category=DeprecationWarning)

    if not direct_output_dir:
        direct_output_dir = folder_naming.get_direct_output_dir(config['run_title'])

    if not indirect_output_dir:
        indirect_output_dir = folder_naming.get_indirect_output_dir(config['run_title'])

    os.makedirs(direct_output_dir, exist_ok=True)
    os.makedirs(indirect_output_dir, exist_ok=True)

    time_now = datetime.now()
    config['time_run'] = str(time_now)
    with open(Path(indirect_output_dir, 'config.json'), 'w') as f:
        json.dump(config, f)

    LOGGER.info(f"Direct output will be saved to {direct_output_dir}")

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

    analysis_df['_direct_impact_already_exists'] = [exists_impact_file(p, config['use_s3']) for p in
                                                    analysis_df['direct_impact_path']]
    analysis_df['_direct_impact_calculate'] = True if config['force_recalculation'] else ~analysis_df[
        '_direct_impact_already_exists']
    n_direct_calculations = np.sum(analysis_df['_direct_impact_calculate'])
    n_direct_exists = np.sum(analysis_df['_direct_impact_already_exists'])

    if config['do_direct']:
        LOGGER.info('\n\nRUNNING DIRECT IMPACT CALCULATIONS')
        LOGGER.info(
            f'There are {n_direct_calculations} direct impacts to calculate. ({n_direct_exists} exist already. Full '
            f'analysis has {analysis_df.shape[0]} impacts.)'
        )

        if config['do_parallel']:
            chunk_size = int(np.ceil(analysis_df.shape[0] / config['ncpus']))
            df_chunked = [analysis_df[i:i + chunk_size] for i in range(0, analysis_df.shape[0], chunk_size)]
            calc_partial = partial(calculate_direct_impacts_from_df, config=config)
            with pa.multiprocessing.ProcessPool(config['ncpus']) as pool:
                pool.map(calc_partial, df_chunked)
        else:
            calculate_direct_impacts_from_df(analysis_df, config)
    else:
        LOGGER.info("Skipping direct impact calculations. Set do_direct: True in your config to change this")

    analysis_df['_direct_impact_exists'] = [exists_impact_file(p, config['use_s3']) for p in
                                            analysis_df['direct_impact_path']]

    analysis_df_filename = f'calculations_report_{time_now.strftime("%Y-%m-%d_%H%M")}.csv'
    analysis_df_path = Path(indirect_output_dir, analysis_df_filename)
    analysis_df.to_csv(analysis_df_path)

    ### ------------------- ###
    ### SAMPLE IMPACT YEARS ###
    ### ------------------- ###

    # Create a yearset for each row of the analysis dataframe
    # This gives us an impact object where each event is a fictional year of events   
    yearset_output_dir = Path(direct_output_dir, "yearsets")
    os.makedirs(yearset_output_dir, exist_ok=True)

    analysis_df['_yearset_already_exists'] = [exists_impact_file(p, config['use_s3']) for p in
                                              analysis_df['yearset_path']]
    analysis_df['_yearset_calculate'] = (True if config['force_recalculation'] else ~analysis_df[
        '_yearset_already_exists']) * analysis_df['_direct_impact_exists']
    n_yearset_calculations = np.sum(analysis_df['_yearset_calculate'])
    n_yearset_exists = np.sum(analysis_df['_yearset_already_exists'])
    n_missing_direct = np.sum(~analysis_df['_yearset_already_exists'] * ~analysis_df['_direct_impact_exists'])

    if config['do_yearsets']:
        LOGGER.info('\n\nCREATING IMPACT YEARSETS')
        LOGGER.info(
            f'There are {n_yearset_calculations} yearsets to create. ({n_yearset_exists} already exist, '
            f'{n_missing_direct} of the remaining are missing direct impact data, full analysis has '
            f'{analysis_df.shape[0]} yearsets.)'
        )

        if config['do_parallel']:
            chunk_size = int(np.ceil(analysis_df.shape[0] / config['ncpus']))
            df_chunked = [analysis_df[i:i + chunk_size] for i in range(0, analysis_df.shape[0], chunk_size)]
            calc_partial = partial(calculate_yearsets_from_df, config=config)
            with pa.multiprocessing.ProcessPool(config['ncpus']) as pool:
                pool.map(calc_partial, df_chunked)
        else:
            calculate_yearsets_from_df(analysis_df, config)
    else:
        LOGGER.info("Skipping yearset calculations. Set do_yearsets: True in your config to change this")

    analysis_df['_yearset_exists'] = [exists_impact_file(p, config['use_s3']) for p in analysis_df['yearset_path']]
    analysis_df.to_csv(analysis_df_path)

    # Next: combine yearsets by hazard to create multihazard yearsets

    # Combine the yearsets for each agriculture crop type to one agriculture yearset
    analysis_df_crop = analysis_df[analysis_df['hazard'].str.contains('relative_crop_yield')]
    analysis_df_no_crop = analysis_df[~analysis_df['hazard'].str.contains('relative_crop_yield')]
    if analysis_df_crop.shape[0] > 0:
        LOGGER.info("\n\nCOMBINING CRP CROP YIELD YEARSETS")
        grouping_cols = ['i_scenario', 'country']
        df_aggregated_yearsets = analysis_df_crop \
            .groupby(grouping_cols)[grouping_cols + ['scenario', 'ref_year', 'yearset_path']] \
            .apply(df_create_combined_hazard_yearsets_agriculture) \
            .reset_index()
        analysis_df = pd.concat([analysis_df_no_crop, df_aggregated_yearsets]).reset_index()

    _ = _check_config_valid_for_indirect_aggregations(config)
    grouping_cols = ['i_scenario', 'sector', 'country']
    if config['do_multihazard']:
        LOGGER.info("\n\nCOMBINING HAZARDS TO MULTIHAZARD YEARSETS")
        df_aggregated_yearsets = analysis_df \
            .groupby(grouping_cols)[grouping_cols + ['hazard', 'scenario', 'ref_year', 'yearset_path']] \
            .apply(df_create_combined_hazard_yearsets) \
            .reset_index()

        analysis_df = pd.concat(
            [analysis_df, df_aggregated_yearsets]
        ).reset_index()  # That's right! I don't know how to use reset_index! # No worries, no one does,
        # but don't forget to call it!
    else:
        LOGGER.info("Skipping multihazard impact calculations. Set do_multihazard: True in your config to change this")

    ### ----------------------------------- ###
    ### CALCULATE INDIRECT ECONOMIC IMPACTS ###
    ### ----------------------------------- ###

    # Generate supply chain impacts from the yearsets
    # Create a folder to output the data
    # indirect_output_dir = Path(indirect_output_dir, "results")
    LOGGER.info("\n\nMODELLING SUPPLY CHAINS")
    os.makedirs(indirect_output_dir, exist_ok=True)

    analysis_df['_indirect_exists'] = False  # TODO: update this to check for existing output
    analysis_df['_indirect_calculate'] = analysis_df['_yearset_exists']

    n_supchain_calculations = np.sum(analysis_df['_indirect_calculate'])
    LOGGER.info(f'There are {n_supchain_calculations} out of {analysis_df.shape[0]} supply chains to calculate')

    # Run the Supply Chain for each country and sector and output the data needed to csv
    if config['do_indirect']:
        for io_a in config['io_approach']:
            # For now we're not parallelising this: looks like there's not much time gained. But should time it
            # properly.
            calculate_indirect_impacts_from_df(analysis_df, io_a, config, direct_output_dir, indirect_output_dir)
    else:
        LOGGER.info("Skipping supply chain calculations. Set do_indirect: True in your config to change this")

    analysis_df.to_csv(analysis_df_path)

    LOGGER.info("\n\nDone!\nTo show the Dashboard run:\nbokeh serve dashboard.py --show")
    LOGGER.info("Don't forget to update the current run title within the dashboard.py script: RUN_TITLE")


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
    df = pd.DataFrame(
        [
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
        ]
    )
    # unfold the agriculture sector into the different crop types
    for crop_type in ["whe", "mai", "ric", "soy"]:
        df_crop_yield = df[df['hazard'] == 'relative_crop_yield'].copy()
        df_crop_yield['sector'] = df_crop_yield['sector'].apply(lambda x: f'{x}_{crop_type}')
        df_crop_yield['hazard'] = df_crop_yield['hazard'].apply(lambda x: f'{x}_{crop_type}')
        df = pd.concat([df, df_crop_yield])
    df = df.reset_index(drop=True)
    # Drop the original agriculture rows
    df = df[df['hazard'] != 'relative_crop_yield']

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


def calculate_direct_impacts_from_df(df, config):
    for _, calc in df.iterrows():
        # TODO subset the df before this check is made. Risk of some parallel processes having no work to do
        if not calc['_direct_impact_calculate']:
            continue

        logging_dict = {k: calc[k] for k in ['hazard', 'sector', 'country', 'scenario', 'ref_year']}
        try:
            imp = nccs_direct_impacts_simple(
                haz_type=calc['hazard'],
                sector=calc['sector'],
                country=calc['country'],
                scenario=calc['scenario'],
                ref_year=calc['ref_year'],
                business_interruption=config['business_interruption'],
                calibrated=config['calibrated'],
                use_sector_bi_scaling=config['use_sector_bi_scaling']
            )
            write_impact_to_file(imp, calc['direct_impact_path'], config['use_s3'])
        except Exception as e:
            LOGGER.error(f"Error calculating direct impacts for {logging_dict}:", exc_info=True)


def calculate_yearsets_from_df(df, config):
    for _, calc in df.iterrows():
        if not calc['_yearset_calculate']:
            continue
        logging_dict = {k: calc[k] for k in ['hazard', 'sector', 'country', 'scenario', 'ref_year']}
        LOGGER.info(f'Generating yearsets for {logging_dict}')
        try:
            imp_yearset = create_single_yearset(
                calc,
                n_sim_years=config['n_sim_years'],
                seed=config['seed'],
            )
            write_impact_to_file(imp_yearset, calc['yearset_path'], config['use_s3'])
        except Exception as e:
            LOGGER.error(f"Error calculating an indirect yearset for {logging_dict}", exc_info=True)


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
    LOGGER.info(r)
    combined_filename = folder_naming.get_direct_namestring(
        prefix='yearset',
        extension='hdf5',
        haz_type='COMBINED',
        sector=r['sector'],
        scenario=r['scenario'],
        ref_year=r['ref_year'],
        country_iso3alpha=r['country']
    )
    combined_path = Path(yearset_output_dir, combined_filename)

    impact_list = [get_impact_from_file(f) for f in df['yearset_path'] if os.path.exists(f)]

    out = {
        'hazard': 'COMBINED',
        'scenario': r['scenario'],
        'ref_year': r['ref_year'],
    }

    if len(impact_list) > 0:
        combined = combine_yearsets(
            impact_list=impact_list,
            cap_exposure=get_sector_exposure(r['sector'], r['country'])
        )
        # TODO drop the impact matrix to save RAM/HD space once SupplyChain is updated and doesn't need it

        combined.write_hdf5(combined_path)
        out['yearset_path'] = combined_path
        out['_yearset_exists'] = True
        # out['annual_impacts'] = combined.at_event
    else:
        out['_yearset_exists'] = False

    return pd.Series(out)


def df_create_combined_hazard_yearsets_agriculture(
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
    LOGGER.info(r)
    combined_filename = folder_naming.get_direct_namestring(
        prefix='yearset',
        extension='hdf5',
        haz_type='relative_crop_yield',
        sector="agriculture",
        scenario=r['scenario'],
        ref_year=r['ref_year'],
        country_iso3alpha=r['country']
    )
    combined_path = Path(yearset_output_dir, combined_filename)

    impact_list = [get_impact_from_file(f) for f in df['yearset_path'] if os.path.exists(f)]

    out = {
        'hazard': 'relative_crop_yield',
        'scenario': r['scenario'],
        'ref_year': r['ref_year'],
        'sector': 'agriculture'
    }

    if len(impact_list) > 0:
        combined = combine_yearsets(
            impact_list=impact_list
        )
        combined.write_hdf5(combined_path)
        out['yearset_path'] = combined_path
        out['_yearset_exists'] = True
        # out['annual_impacts'] = combined.at_event
    else:
        out['_yearset_exists'] = False

    return pd.Series(out)


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
    imp = get_impact_from_file(row['direct_impact_path'])

    poisson_hazards = ['tropical_cyclone', 'sea_level_rise']
    poisson = row['hazard'] in poisson_hazards

    # TODO we don't actually want to generate a yearset if we're looking at observed events
    imp_yearset = yearset_from_imp(
        imp,
        n_sim_years,
        poisson=poisson,
        cap_exposure=get_sector_exposure(row['sector'], row['country']),
        seed=seed
    )
    # TODO drop the impact matrix to save RAM/HD space once SupplyChain is updated and doesn't need it
    return imp_yearset


def calculate_indirect_impacts_from_df(df, io_a, config, direct_output_dir, indirect_output_dir):
    # TODO consider some sort of grouping so that we don't need to load sector exposures each time...
    # No need to parallelise this: it already seems to max out the CPUs
    for i, row in df.iterrows():
        logging_dict = {k: row[k] for k in ['hazard', 'sector', 'country', 'scenario', 'ref_year']}

        if not row['_indirect_calculate']:
            LOGGER.info('No yearset data available. Skipping supply chain calculation')
            continue

        # TODO put this in a function: it's used in the supply_chain_climada method too
        country_iso3alpha = pycountry.countries.get(name=row['country']).alpha_3
        supchain_indirect_output_path = f"{indirect_output_dir}/" \
           f"indirect_impacts" \
           f"_{row['hazard']}" \
           f"_{row['sector'].replace(' ', '_')[:15]}" \
           f"_{row['scenario']}" \
           f"_{row['ref_year']}" \
           f"_{io_a}" \
           f"_{country_iso3alpha}" \
           f".csv"

        if os.path.exists(supchain_indirect_output_path):
            LOGGER.info(f'Output already exists, skipping calculation: {supchain_indirect_output_path}')
            continue

        try:
            LOGGER.info(f"Calculating indirect {io_a} supply chain for {logging_dict}...")
            imp = Impact.from_hdf5(row['yearset_path'])

            if not imp.at_event.any():
                # TODO return an object with zero losses so that there's data
                LOGGER.info("No non-zero impacts. Skipping")
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
            LOGGER.error(f"Error calculating indirect impacts for {logging_dict}:", exc_info=True)


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
        raise ValueError(
            'To continue with generation of yearsets and indirect impacts, the config needs to have the ' \
            'same number of scenarios specified for each hazard in the config, or just one scenario.'
        )
    return 1 if len(n_scenarios_list) == 0 else n_scenarios_list[0]


if __name__ == "__main__":
    # This is the full run
    # from run_configurations.config import CONFIG

    # This is for testing
    from run_configurations.test_config import CONFIG2  # change here to test_config if needed

    run_pipeline_from_config(CONFIG2)
