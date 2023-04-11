from climada.util.api_client import Client
from climada_petals.engine import SupplyChain
from climada.entity import ImpfTropCyclone, ImpactFuncSet
from climada.engine.impact_calc import ImpactCalc

from supply_chain.compute import compute_supply_chain
from supply_chain.visualization import create_supply_chain_vis
def main():
    client = Client()

    ### ------------------------------------ ###
    ### 1. CALCULATE DIRECT ECONOMIC IMPACTS ###
    ### ------------------------------------ ###

    exp_usa = client.get_litpop('USA')

    tc_usa = client.get_hazard('tropical_cyclone', properties={'country_iso3alpha':'USA', 'climate_scenario':'historical'})

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
    supchain = compute_supply_chain(direct_impact_usa, exp_usa)

    # Everything in this section equivalent to
    #    supchain.calc_production_impacts(direct_impact_usa, exp_usa, impacted_secs=impacted_secs, io_approach='ghosh')
    create_supply_chain_vis(supchain)

if __name__ == "__main__":
    main()