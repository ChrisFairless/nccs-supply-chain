import os

import pandas as pd
from climada_petals.engine import SupplyChain

SERVICE_SEC = {"service": range(26, 56)}


def supply_chain_climada(exposure, direct_impact, impacted_sector="service", io_approach='ghosh', shock_factor=None):
    assert impacted_sector in SERVICE_SEC.keys(), f"impacted_sector must be one of {SERVICE_SEC.keys()}"
    sec_range = SERVICE_SEC[impacted_sector]
    supchain: SupplyChain = SupplyChain.from_mriot(mriot_type='WIOD16', mriot_year=2011)

    # Assign exposure and stock direct_impact to MRIOT country-sector

    # (Service sector)
    impacted_secs = supchain.mriot.get_sectors()[sec_range].tolist()
    supchain.calc_shock_to_sectors(
        exposure=exposure,
        impact=direct_impact,
        impacted_secs=impacted_secs,
        shock_factor=shock_factor
    )  # renamed the function from
    # calc_secs_exp_imp_shock since the code changed

    # Calculate the propagation of production losses
    supchain.calc_impacts(
        exposure=exposure,
        impact=direct_impact,
        io_approach=io_approach,
        impacted_secs=impacted_secs
    )
    return supchain


def dump_supchain_to_csv(supchain, haz_type, country, sector):
    indirect_impacts = [
        {
            "sector": sec[1],
            "value": v,
            "hazard_type": haz_type,
            "country_of_impact": country,
            "sector_of_impact": sector
        }
        for (sec, v) in supchain.supchain_imp["ghosh"].loc[:, ('CHE', slice(None))].max(0).items()
    ]
    df_indirect = pd.DataFrame(indirect_impacts)
    path = f"{os.path.dirname(__file__)}/results/" \
           f"indirect_impacts" \
           f"_{haz_type}" \
           f"_{country.replace(' ', '_')[:15]}" \
           f"_{sector.replace(' ', '_')[:15]}" \
           f".csv"

    df_indirect.to_csv(path)
    return path
