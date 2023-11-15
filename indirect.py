import os

import numpy as np
import pandas as pd
import pycountry
from climada_petals.engine import SupplyChain

# original
# SERVICE_SEC = {"service": range(26, 56)}
SUPER_SEC = {
    "manufacturing": range(4, 22),
    "service": range(26, 56),
    "mining": [3],
    "electricity": [23],
}


def get_country_modifier(supchain: SupplyChain, country_iso3alpha, n_total=195):
    """
    Calculate the country modifier for a given country in a supply chain.
    If the country is listed in the mrio table then the modifier is 1.0.
    else the modifier is 1 / (n_total - (number of countries in the mrio table - 1)).

    :param supchain: 
    :param country_iso3alpha: 
    :param n_total: 
    :return: 
    """
    mrio_region = supchain.map_exp_to_mriot(country_iso3alpha, "WIOD16")
    if mrio_region == 'ROW':
        return 1 / (n_total - (len(set(r[0] for r in supchain.mriot.x.axes[0])) - 1))
    return 1.0


def get_supply_chain() -> SupplyChain:
    return SupplyChain.from_mriot(mriot_type='WIOD16', mriot_year=2011)


def supply_chain_climada(exposure, direct_impact, io_approach, impacted_sector="service", shock_factor=None):
    assert impacted_sector in SUPER_SEC.keys(), f"impacted_sector must be one of {SUPER_SEC.keys()}"
    sec_range = SUPER_SEC[impacted_sector]
    supchain: SupplyChain = get_supply_chain()

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



def dump_supchain_to_csv(supchain, haz_type, sector, scenario, ref_year, country, n_sim=100, return_period=100, io_approach='ghosh'):
    index_rp = np.floor(n_sim / return_period).astype(int) - 1
    indirect_impacts = []
    for (sec, v) in supchain.supchain_imp[f"{io_approach}"].loc[:, ('CHE', slice(None))].items():
        rp_value = v.sort_values(ascending=False).iloc[index_rp]
        mean = v.sum() / n_sim
        max_val = v.max()

        obj = {
            "sector": sec[1],
            #"value": mean,
            "impact_max": max_val,
            "impact_aai": mean,
            f"impact_rp_{return_period}": rp_value,
            "hazard_type": haz_type,
            "sector_of_impact": sector,
            "scenario": scenario,
            "ref_year": ref_year,
            "country_of_impact": country,

        }
        indirect_impacts.append(obj)


    df_indirect = pd.DataFrame(indirect_impacts)
    # newly added to get ISO3 code
    country_iso3alpha = pycountry.countries.get(name=country).alpha_3  # f"_{country.replace(' ', '_')[:15]}" \
    path = f"{os.path.dirname(__file__)}/results/" \
           f"indirect_impacts" \
           f"_{haz_type}" \
           f"_{sector.replace(' ', '_')[:15]}" \
           f"_{scenario}" \
           f"_{ref_year}" \
           f"_{io_approach}" \
           f"_{country_iso3alpha}" \
           f".csv"

    df_indirect.to_csv(path)

    supchain.supchain_imp[f"{io_approach}"]
    return path
