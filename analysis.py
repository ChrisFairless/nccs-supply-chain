import os.path
import numpy as np
import pandas as pd
from typing import List

from climada.util.api_client import Client
from climada_petals.engine import SupplyChain
from climada.entity import ImpfTropCyclone, ImpactFuncSet, Exposures
from climada.engine.impact_calc import ImpactCalc
from climada.entity import ImpactFuncSet, ImpfTropCyclone
from climada.util.api_client import Client

from indirect_impacts.compute import supply_chain_climada
from indirect_impacts.visualization import create_supply_chain_vis
from utils.s3client import download_from_s3_bucket, upload_to_s3_bucket
from direct_impacts.direct import nccs_direct_impacts_list_simple, get_sector_exposure
from direct_impacts.calc_yearset import nccs_yearsets_simple

country_list = ['United States', 'China']
hazard_list = ['tropical_cyclone', 'river_flood']
sector_list = ['service', 'service']
scenario = 'rcp60'
ref_year = 2080
n_sim_years = 5000

# country_list = ['Saint Kitts and Nevis']
# hazard_list = ['tropical_cyclone']
# sector_list = ['service']
# scenario = 'rcp60'
# ref_year = 2080
# n_sim_years = 50

job_name: str = 'test'
save_intermediate_dir = './scratch'
save_intermediate_s3 = False
load_saved_objects = True
overwrite = False
return_impact_objects = False
seed = 1312


def calc_supply_chain_impacts(
        country_list: List[str],
        hazard_list: List[str],
        sector_list: List[str],
        scenario: str,
        ref_year: int,
        n_sim_years: int,
        job_name: str = 'test',
        save_intermediate_dir: str = None,
        save_intermediate_s3: bool = False,
        load_saved_objects: bool = True,
        overwrite: bool = True,
        return_impact_objects: bool = False,
        seed: int = 1312
):
    """
    Run an end-to-end supply chain calculation.

    For each combination of country, hazard, and sector provided in the first three parameters, generate impact objects 
    for the probabilistic event sets and calculate the indirect supply chain impacts. Impact functions are inferred 
    using the `get_sector_impf` method in the direct module. Intermediate files are saved if a path or an S3 bucket 
    name is provided to the `save_intermediate_dir` or `save_intermediate_s3` parameters.

    Parameters
    ----------
    country_list : list of str
        List of countries to analyse, either as names or three-letter ISO code. Names should be consistent with the 
        pycountry module.
    hazard_list : list of str
        List of hazards to analyse. Passed to direct.get_hazard to query the CLIMADA Data API.
    sector_list : list of str
        List of sectors to analyse. Passed to direct.get_sector_exposure.
    scenario : str
        Climate scenario to analyse. Currently one of 'historical', 'ssp126', 'ssp245', 'ssp560'.
    ref_year : int
        Year to simulate. One of '2020', '2040', '2060', '2080'.
    n_sim_years : int
        Number of simulated years of events to create in the simulated yearset.
    job_name  : str
        A string used to create output filenames. They follow the format <jobname>_<product>_<hazard>_<sector>_<country>
        e.g. a jobname of 'test' could create test_impact_tropicalcyclone_agriculture_USA.hdf5. Default 'test'
    save_intermediate_dir : str
        If you want to save intermediate files locally, the directory to save them in. Filenames are set using the 
        `job_name` parameter. Default None
    save_intermediate_s3 : bool
        If you want to save intermediate files to an S3 bucket. Uses credentials stored in .env. Filenames are set 
        using the `job_name` parameter. Default False
    load_saved_objects : bool
        If results have already been calculated, analysis expects to find existing files (at all stages), 

    seed : int
    """

    ### --------------------------------- ###
    ### CALCULATE DIRECT ECONOMIC IMPACTS ###
    ### --------------------------------- ###

    # Generate a data frame with metadata, exposure objects and impact objects 
    # for each combination of input factors.
    analysis_df = nccs_direct_impacts_list_simple(
        hazard_list=hazard_list, 
        sector_list=sector_list,
        country_list=country_list,
        scenario=scenario,
        ref_year=ref_year,
        job_name=job_name,
        save_intermediate_dir=save_intermediate_dir,
        save_intermediate_s3=save_intermediate_s3,
        load_saved_objects=load_saved_objects,
        overwrite=overwrite,
        return_impact_objects=return_impact_objects
    )

    ### ------------------- ###
    ### SAMPLE IMPACT YEARS ###
    ### ------------------- ###

    # Sample impact objects to create a yearset for each row of the data frame
    analysis_df = nccs_yearsets_simple(
        analysis_df=analysis_df, 
        n_sim_years=n_sim_years,
        save_intermediate_dir=save_intermediate_dir,
        save_intermediate_s3=save_intermediate_s3,
        load_saved_objects=load_saved_objects,
        overwrite=overwrite,
        return_impact_objects=return_impact_objects,
        seed=seed
    )

    ### ----------------------------------- ###
    ### CALCULATE INDIRECT ECONOMIC IMPACTS ###
    ### ----------------------------------- ###

    # Generate supply chain impacts from the yearsets
    # Create a folder to output the data
    os.makedirs("results", exist_ok=True)

    # Run the Supply Chain for each country and sector and output the data needed to csv
    for _, row in analysis_df.iterrows():
        supchain = supply_chain_climada(
            get_sector_exposure(sector=row['sector'], country=row['country']),
            row['impact_yearset'],
            impacted_sector=row['sector'],
            io_approach='ghosh'
        )
        dump_supchain_to_csv(supchain, row['haz_type'], row['country'], row['sector'])
    print("Done!\nTo show the Dashboard run:\nbokeh serve dashboard.py --show")



if __name__ == "__main__":
    calc_supply_chain_impacts(
        country_list,
        hazard_list,
        sector_list,
        scenario,
        ref_year,
        n_sim_years,
        job_name='test_main'
    )
