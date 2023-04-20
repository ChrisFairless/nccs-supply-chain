from climada_petals.engine import SupplyChain

SERVICE_SEC = {"service": range(26, 56)}

def supply_chain_climada(exposure, direct_impact, impacted_sector="service", io_approach='ghosh'):
    assert impacted_sector in SERVICE_SEC.keys(), f"impacted_sector must be one of {SERVICE_SEC.keys()}"
    sec_range = SERVICE_SEC[impacted_sector]
    supchain = SupplyChain.from_mriot(mriot_type='WIOD16', mriot_year=2011)

    # Assign exposure and stock direct_impact to MRIOT country-sector

    # (Service sector)
    impacted_secs = supchain.mriot.get_sectors()[sec_range].tolist()
    supchain.calc_secs_exp_imp_shock(exposure, direct_impact, impacted_secs)

    # Calculate local production losses
    supchain.calc_direct_production_impacts()

    # Calculate the propagation of production losses
    supchain.calc_indirect_production_impacts(direct_impact.event_id, io_approach=io_approach)

    # Calculate total production loss
    supchain.calc_total_production_impacts()

    supchain.calc_production_eai(direct_impact.frequency)

    return supchain
