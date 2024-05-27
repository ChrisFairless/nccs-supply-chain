import os.path

from pipeline.direct.calc_yearset import nccs_yearsets_simple
# from utils.s3client import download_from_s3_bucket, upload_to_s3_bucket
from pipeline.direct.direct import get_sector_exposure, nccs_direct_impacts_list_simple
from pipeline.indirect.indirect import dump_direct_to_csv, dump_supchain_to_csv, supply_chain_climada
from utils import folder_naming


def calc_supply_chain_impacts(
        country_list,
        hazard_list,
        sector_list,
        scenario,
        ref_year,
        n_sim_years,
        io_approach,
        save_by_country=False,
        save_by_hazard=False,
        save_by_sector=False,
        seed=1312,
        indirect_output_dir="results/indirect",
        direct_output_dir="results/direct"
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
    analysis_df['impact_yearset'] = nccs_yearsets_simple(
        analysis_df['impact_eventset'],
        n_sim_years, seed=seed
    )

    ### ----------------------------------- ###
    ### CALCULATE INDIRECT ECONOMIC IMPACTS ###
    ### ----------------------------------- ###

    # Generate supply chain impacts from the yearsets
    # Create a folder to output the data
    os.makedirs("results", exist_ok=True)

    # Run the Supply Chain for each country and sector and output the data needed to csv
    for io_a in io_approach:
        for _, row in analysis_df.iterrows():
            try:
                print(f"Calculating indirect impacts for {row['country']} {row['sector']}...")
                supchain = supply_chain_climada(
                    get_sector_exposure(sector=row['sector'], country=row['country']),
                    row['impact_yearset'],
                    impacted_sector=row['sector'],
                    io_approach=io_a
                )
                # save direct impacts to a csv
                dump_direct_to_csv(
                    supchain=supchain,
                    haz_type=row['haz_type'],
                    sector=row['sector'],
                    scenario=scenario,
                    ref_year=ref_year,
                    country=row['country'],
                    n_sim=n_sim_years,
                    return_period=100,
                    output_dir=direct_output_dir
                )
                # save indirect impacts to a csv
                dump_supchain_to_csv(
                    supchain=supchain,
                    haz_type=row['haz_type'],
                    sector=row['sector'],
                    scenario=scenario,
                    ref_year=ref_year,
                    country=row['country'],
                    n_sim=n_sim_years,
                    return_period=100,
                    io_approach=io_a,
                    output_dir=indirect_output_dir
                )

            except ValueError as e:
                print(f"Error calculating indirect impacts for {row['country']} {row['sector']}: {e}")

    print("Done!\nTo show the Dashboard run:\nbokeh serve dashboard.py --show")
    print("Don't forget to update the current run title within the dashboard.py script: RUN_TITLE")


def run_pipeline(country_list,
                 hazard,
                 sector_list,
                 scenario,
                 ref_year,
                 n_sim_years,
                 io_approach,
                 direct_output_dir,
                 indirect_output_dir):
    for country in country_list:
        try:
            calc_supply_chain_impacts(
                [country],  # replace by country_list if whole list should be calculated at once
                [hazard],
                sector_list,
                scenario,
                ref_year,
                n_sim_years,
                io_approach,
                direct_output_dir=direct_output_dir,
                indirect_output_dir=indirect_output_dir
            )
        except Exception as e:
            print(f"Could not calculate country {country} {sector_list} due to {e}")
            #raise e
    print("Done!\nTo show the Dashboard run:\nbokeh serve dashboard.py --show")


def run_pipeline_from_config(config):

    direct_output_dir = folder_naming.get_direct_output_dir(config['run_title'])
    indirect_output_dir = folder_naming.get_indirect_output_dir(config['run_title'])

    os.makedirs(direct_output_dir, exist_ok=True)
    os.makedirs(indirect_output_dir, exist_ok=True)
    print(f"Direct output will be saved to {direct_output_dir}")

    for run in config["runs"]:
        for scenario_year in run["scenario_years"]:
            run_pipeline(
                run["countries"],
                run["hazard"],
                run["sectors"],
                scenario_year["scenario"],
                scenario_year["ref_year"],
                config["n_sim_years"],
                run["io_approach"],
                direct_output_dir=direct_output_dir,
                indirect_output_dir=indirect_output_dir
            )


if __name__ == "__main__":
    # This is the full run
    # from run_configurations.config import CONFIG

    # This is for testing
    from run_configurations.test_config import CONFIG  # change here to test_config if needed

    run_pipeline_from_config(CONFIG)
