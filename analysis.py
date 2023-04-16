import numpy as np
import pandas as pd

from climada.util.api_client import Client
from climada_petals.engine import SupplyChain
from climada.entity import ImpfTropCyclone, ImpactFuncSet, Exposures
from climada.engine.impact_calc import ImpactCalc
from climada.entity import ImpactFuncSet, ImpfTropCyclone
from climada.util.api_client import Client

from indirect_impacts.compute import supply_chain_climada
from indirect_impacts.visualization import create_supply_chain_vis
from utils.s3client import download_from_s3_bucket, upload_to_s3_bucket
from direct import nccs_direct_impacts_list_simple
from calc_yearset import nccs_yearsets_simple

country_list = ['Saint Kitts and Nevis', 'Jamaica']
hazard_list = ['tropical_cyclone', 'river_flood']
sector_list = ['service', 'service']
scenario = 'rcp60'
ref_year = 2080
n_sim_years = 100

def calc_supply_chain_impacts(
        country_list,
        hazard_list,
        sector_list,
        scenario,
        ref_year,
        n_sim_years,
        save_by_country=False,
        save_by_hazard=False,
        save_by_sector=False,
        seed=1312
):

    ### --------------------------------- ###
    ### CALCULATE DIRECT ECONOMIC IMPACTS ###
    ### --------------------------------- ###

    # Generate a data frame with metadata, exposure objects and impact objects 
    # for each combination of input factors.
    analysis_df = nccs_direct_impacts_list_simple(hazard_list, sector_list, country_list, scenario, ref_year)

    ### ------------------- ###
    ### SAMPLE IMPACT YEARS ###
    ### ------------------- ###

    # Sample impact objects to create a yearset for each row of the data frame
    analysis_df['yearset'] = nccs_yearsets_simple(analysis_df['impact'], n_sim_years, seed=seed)

    ### ----------------------------------- ###
    ### CALCULATE INDIRECT ECONOMIC IMPACTS ###
    ### ----------------------------------- ###

    # Generate supply chain impacts from the yearsets
    analysis_df['supchain'] = [
        supply_chain_climada(row['exp'], row['yearset'], impacted_sector=row['sector'], io_approach='ghosh')
        for _, row in analysis_df.iterrows()
    ]

    # Everything in this section equivalent to
    #    supchain.calc_production_impacts(direct_impact_usa, exp_usa, impacted_secs=impacted_secs, io_approach='ghosh')
    create_supply_chain_vis(supchain)


if __name__ == "__main__":
    calc_supply_chain_impacts(
        country_list,
        hazard_list,
        sector_list,
        scenario,
        ref_year
    )
