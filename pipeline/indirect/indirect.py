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
    "agriculture": [0],
    "forestry": [1]
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


def get_secs_prod(supchain: SupplyChain, country_iso3alpha, impacted_secs, n_total=195):
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
        return (1 / (n_total - (len(set(r[0] for r in supchain.mriot.x.axes[0])) - 1)))*supchain.mriot.x.loc[("ROW", impacted_secs), :]
    return supchain.mriot.x.loc[(country_iso3alpha, impacted_secs), :]

def get_secs_shock(supchain: SupplyChain, country_iso3alpha, impacted_secs, n_total=195):
    """
    Calculate the country modifier for a given country in a supply chain.
    If the country is listed in the mrio table then the modifier is 1.0.
    else the modifier is 1 / (n_total - (number of countries in the mrio table - 1)).

    :param supchain:
    :param country_iso3alpha:
    :param n_total:
    :return:

    Definitions:
    secs_imp : pd.DataFrame
        Impact dataframe for the directly affected countries/sectors for each event with
        impacts. Columns are the same as the chosen MRIOT and rows are the hazard events ids.

    secs_shock : pd.DataFrame
        Shocks (i.e. impact / exposure) dataframe for the directly affected countries/sectors
        for each event with impacts. Columns are the same as the chosen MRIOT and rows are the
        hazard events ids.
    """
    #TODO check if which one should be used: secs_shock or secs_imp (see definitions above)
    # I would argue to still use secs_shock as it accounts for the exposure impact ratio (The attribute
    # self.secs_shock is proportional to the ratio between self.secs_imp and self.secs_exp, so self.secs_shock
    # is a number between 0 and 1. self.secs_shock will be used in the indirect impact calculation to assses
    # how much production loss is experienced by each sector.)
    # if using secs_shock again, the value extractions would need to change again


    mrio_region = supchain.map_exp_to_mriot(country_iso3alpha, "WIOD16")
    if mrio_region == 'ROW':
        return (1 / (n_total - (len(set(r[0] for r in supchain.mriot.x.axes[0])) - 1)))*supchain.secs_shock.loc[:, ("ROW", impacted_secs)] #TODO secs_shock vs secs_imp
    return supchain.secs_shock.loc[:, (country_iso3alpha, impacted_secs)] #TODO secs_shock vs secs_imp

def get_supply_chain() -> SupplyChain:
    return SupplyChain.from_mriot(mriot_type='WIOD16', mriot_year=2011)


def supply_chain_climada(exposure, direct_impact, io_approach, impacted_sector="service", shock_factor=None):
    assert impacted_sector in SUPER_SEC.keys(), f"impacted_sector must be one of {SUPER_SEC.keys()}"
    sec_range = SUPER_SEC[impacted_sector]
    supchain: SupplyChain = get_supply_chain()

    # Assign exposure and stock direct_impact to MRIOT country-sector

    #
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


def dump_direct_to_csv(supchain,
                       haz_type,
                       sector,
                       scenario,
                       ref_year,
                       country,
                       n_sim=100,
                       return_period=100,
                       output_dir="results/direct"):
    index_rp = np.floor(n_sim / return_period).astype(int) - 1
    direct_impacts = []

    sec_range = SUPER_SEC[sector]
    impacted_secs = supchain.mriot.get_sectors()[sec_range].tolist()
    country_iso3alpha = pycountry.countries.get(name=country).alpha_3
    # calls the function which is especially important for ROW countries as the country code does not exist
    secs_prod = get_secs_prod(supchain, country_iso3alpha, impacted_secs)
    # create a lookup table for each sector and its total production
    lookup = {}
    for idx, row in secs_prod.iterrows():
        lookup[idx] = row["total production"]

    for (sec, v) in get_secs_shock(supchain, country_iso3alpha, impacted_secs).items():
        # TODO What to do about the exposure units, Litpop exposure is in USD, is the direct impact then also in USD?
        # TODO If using secs_shock, we would need to divide the impacts by 1 Million, as the total production of the mrio is in MEUR
        rp_value = v.sort_values(ascending=False).iloc[index_rp]  # TODO cehck if / 1000000  is required
        mean_ratio = (v.sum() / n_sim)  # TODO cehck if / 1000000  is required
        max_val = v.max()  # TODO cehck if / 1000000  is required

        # Check if the denominator is non-zero before performing division

        total_production = lookup[sec]
        obj = {
            "sector": sec[1],
            "total_sectorial_production_mriot": lookup[sec],

            "maxPL": max_val * total_production, # TODO: check if this is correct, using secs_shock would only require max_val
            "rmaxPL": max_val * 100, # TODO: check if this correct, secs_shock would need (max_val / total_production)*100
            "AAPL": mean_ratio * total_production, # TODO: check if this is correct, secs_shock would only require mean_ratio
            "rAAPL": mean_ratio * 100, # TODO: check if this is correct, secs_shock wpuld require: (mean_ratio / total_production)*100
            f"PL{return_period}": rp_value * total_production,  # TODO: check if this is correct,
            f"rPL{return_period}": rp_value * 100,  # TODO: check if this is correct,
            "hazard_type": haz_type,
            "sector_of_impact": sector,
            "scenario": scenario,
            "ref_year": ref_year,
            "country_of_impact": country,
        }

        direct_impacts.append(obj)

    df_direct = pd.DataFrame(direct_impacts)
    # newly added to get ISO3 code

    path = f"{output_dir}/" \
           f"direct_impacts" \
           f"_{haz_type}" \
           f"_{sector.replace(' ', '_')[:15]}" \
           f"_{scenario}" \
           f"_{ref_year}" \
           f"_{country_iso3alpha}" \
           f".csv"

    df_direct.to_csv(path)
    return path


def dump_supchain_to_csv(supchain,
                         haz_type,
                         sector,
                         scenario,
                         ref_year,
                         country,
                         io_approach,
                         n_sim=100,
                         return_period=100,
                         output_dir="results/indirect"):
    index_rp = np.floor(n_sim / return_period).astype(int) - 1
    indirect_impacts = []

    # total production of each sector for country in Millions

    secs_prod = supchain.mriot.x.loc[("CHE"), :]

    country_iso3alpha = pycountry.countries.get(name=country).alpha_3
    rotw_factor = get_country_modifier(supchain, country)

    # create a lookup table for each sector and its total production
    lookup = {}
    for idx, row in secs_prod.iterrows():
        lookup[idx] = row["total production"]

    for (sec, v) in supchain.supchain_imp[f"{io_approach}"].loc[:, ('CHE', slice(None))].items():

        # We scale all values such that countries in the rest of the world category
        # are divided evenly by the number of countries in ROW. Countries explicitely in the MRIO
        # table have a rotw_factor of 1
        #TODO check again the units of the output, does the exposure value unit match the mriot value unit?
        rp_value = v.sort_values(ascending=False).iloc[index_rp] * rotw_factor
        mean = (v.sum() / n_sim) * rotw_factor
        max_val = v.max() * rotw_factor


        total_production = lookup[sec[1]]    #no muliply with the rotw fctor, since we use the Swiss productions
        obj = {
            "sector": sec[1],
            "total_sectorial_production_mriot_CHE": total_production,
            "imaxPL": max_val,
            "irmaxPL": (max_val / total_production) * 100 if total_production != 0 else 0,
            "iAAPL": mean,
            "irAAPL": (mean / total_production) * 100 if total_production != 0 else 0,
            f"iPL{return_period}": rp_value,
            f"irPL{return_period}": (rp_value / total_production) * 100 if total_production != 0 else 0,
            "hazard_type": haz_type,
            "sector_of_impact": sector,
            "scenario": scenario,
            "ref_year": ref_year,
            "country_of_impact": country,
            "io_approach": io_approach
        }
        indirect_impacts.append(obj)

    df_indirect = pd.DataFrame(indirect_impacts)

    # newly added to get ISO3 code
    path = f"{output_dir}/" \
           f"indirect_impacts" \
           f"_{haz_type}" \
           f"_{sector.replace(' ', '_')[:15]}" \
           f"_{scenario}" \
           f"_{ref_year}" \
           f"_{io_approach}" \
           f"_{country_iso3alpha}" \
           f".csv"
    df_indirect.to_csv(path)
    return path
