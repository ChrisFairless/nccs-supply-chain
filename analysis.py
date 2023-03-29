from climada.util.api_client import Client
from climada_petals.engine import SupplyChain
from climada.entity import ImpfTropCyclone, ImpactFuncSet
from climada.engine.impact_calc import ImpactCalc

def main():
    client = Client()

    ### ------------------------------------ ###
    ### 1. CALCULATE DIRECT ECONOMIC IMPACTS ###
    ### ------------------------------------ ###

    exp_usa = client.get_litpop('USA')

    tc_usa = client.get_hazard('tropical_cyclone', properties={'country_iso3alpha':'USA', 'climate_scenario':'historical'})

    # Define impact function
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

    supchain = SupplyChain.from_mriot(mriot_type='WIOD16', mriot_year=2011)

    # Assign exposure and stock impact to MRIOT country-sector
    
    # (Service sector)
    impacted_secs = supchain.mriot.get_sectors()[range(26,56)].tolist()
    supchain.calc_secs_exp_imp_shock(exp_usa, direct_impact_usa, impacted_secs)

    # Calculate local production losses
    supchain.calc_direct_production_impacts(direct_impact_usa)

    # Calculate the propagation of production losses
    supchain.calc_indirect_production_impacts(direct_impact_usa, io_approach='ghosh')

    # Calculate total production loss
    supchain.calc_total_production_impacts(direct_impact_usa)


    # Everything in this section equivalent to
    #    supchain.calc_production_impacts(direct_impact_usa, exp_usa, impacted_secs=impacted_secs, io_approach='ghosh')


if __name__ == "__main__":
    main()