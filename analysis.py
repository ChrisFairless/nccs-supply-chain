from climada.engine.impact_calc import ImpactCalc
from climada.entity import ImpactFuncSet, ImpfTropCyclone
from climada.util.api_client import Client

from indirect_impacts.compute import supply_chain_climada
from indirect_impacts.visualization import create_supply_chain_vis
from utils.s3client import download_from_s3_bucket, upload_to_s3_bucket


def main():

    # @chris to fetch some data: Make sure to set the environment variables first
    #  (see .sample_dotenv and utils.s3client.py) I have no access rights to do this
    #  (don't see any access tokens on my page, only a warning "no access")
    # with open("test.txt", "w") as f:
    #     f.write("test")
    #
    # upload_to_s3_bucket(input_filepath="test.txt", s3_filename="my-data-asset")
    # download_from_s3_bucket(s3_filename="my-data-asset", output_path="test2.txt")
    #
    # os.remove("test.txt")
    # os.remove("test2.txt")

    client = Client()

    ### ------------------------------------ ###
    ### 1. CALCULATE DIRECT ECONOMIC IMPACTS ###
    ### ------------------------------------ ###

    exp_usa = client.get_litpop('USA')

    tc_usa = client.get_hazard(
        'tropical_cyclone',
        properties={'country_iso3alpha': 'USA', 'climate_scenario': 'historical'}
    )

    # Define direct_impact function
    impf_tc = ImpfTropCyclone.from_emanuel_usa()
    impf_set = ImpactFuncSet()
    impf_set.append(impf_tc)
    impf_set.check()

    # Calculate direct impacts to the USA due to TC
    imp_calc = ImpactCalc(exp_usa, impf_set, tc_usa)
    direct_impact_usa = imp_calc.impact()

    ### ----------------------------------- ###
    ### CALCULATE INDIRECT ECONOMIC IMPACTS ###
    ### ----------------------------------- ###
    supchain = supply_chain_climada(exp_usa, direct_impact_usa, impacted_sector="service", io_approach='ghosh')

    # Everything in this section equivalent to
    #    supchain.calc_production_impacts(direct_impact_usa, exp_usa, impacted_secs=impacted_secs, io_approach='ghosh')
    create_supply_chain_vis(supchain)


if __name__ == "__main__":
    main()
