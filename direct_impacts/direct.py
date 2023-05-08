import pandas as pd
from pathlib import Path
from climada.util.api_client import Client
from climada_petals.engine import SupplyChain
from climada.entity import ImpfTropCyclone, ImpactFuncSet, Exposures
from climada.engine.impact_calc import ImpactCalc
from climada_petals.entity.impact_funcs.river_flood import flood_imp_func_set

from direct_impacts.io import save_impact, load_impact, get_job_filename, standardise_country

HAZ_TYPE_LOOKUP = {
    'tropical_cyclone': 'TC',
    'river_flood': 'RF'
}


# Method to loop through configuration lists of and run an impact calculation for each combination on the list
# Simple, but can be sped up and memory usage reduced
def nccs_direct_impacts_list_simple(
        hazard_list,
        sector_list,
        country_list,
        scenario,
        ref_year,
        job_name,
        save_intermediate_dir,
        save_intermediate_s3,
        load_saved_objects,
        overwrite,
        return_impact_objects
        ):
    
    job_list = []
    for haz_type in hazard_list:
        for sector in sector_list:
            for country in country_list:
                file_name_eventset = get_job_filename(job_name, 'eventset', HAZ_TYPE_LOOKUP[haz_type], scenario, ref_year, sector, country, 'hdf5')
                if load_saved_objects:
                    if return_impact_objects:
                        impact_eventset = load_impact(file_name_eventset, save_intermediate_dir, save_intermediate_s3)
                    else:
                        impact_eventset = None
                else:
                    impact_eventset=nccs_direct_impacts_simple(haz_type, sector, country, scenario, ref_year)
                    if save_intermediate_dir or save_intermediate_s3:
                        save_impact(impact_eventset, file_name_eventset, save_intermediate_dir, save_intermediate_s3, overwrite)
                    if not return_impact_objects:
                        impact_eventset = None
                job_list.append(
                    dict(
                        haz_type=haz_type,
                        sector=sector,
                        country=country,
                        country_iso3alpha=standardise_country(country),
                        scenario=scenario,
                        ref_year=ref_year,
                        impact_eventset=impact_eventset,
                        file_name_eventset=file_name_eventset
                    )
                )
    return pd.DataFrame(job_list)


def nccs_direct_impacts_simple(haz_type, sector, country, scenario, ref_year):
    country_iso3alpha = standardise_country(country)
    haz = get_hazard(haz_type, country_iso3alpha, scenario, ref_year)
    exp = get_sector_exposure(sector, country)
    impf_set = get_sector_impf_set(haz_type, sector, country)
    return ImpactCalc(exp, impf_set, haz).impact(save_mat=True)


def get_sector_exposure(sector, country):
    if sector == 'service':
        client = Client()
        exp = client.get_litpop(country)
        exp.gdf['value'] = exp.gdf['value'] # / 100
        exp.tag.description = '_'.join([sector, country]) 
        return exp
    else:
        raise ValueError('Sector not recognised')
    # add more sectors


def get_sector_impf_set(hazard, sector, country):
    return ImpactFuncSet([get_sector_impf(hazard, sector, country)])


def get_sector_impf(hazard, sector, country):
    # TODO: load regional impfs based on country and
    # sector-specific impfs when they'll be available
    if hazard == "tropical_cyclone":
        impf = ImpfTropCyclone.from_emanuel_usa()       # US TC impacts (for now)
    elif hazard == "river_flood":
        impf = flood_imp_func_set().get_func(fun_id=3)  # EU Flood impacts (for now)
    else:
        raise ValueError(f"We didn't add impact functions for {hazard}")
    impf.haz_type = HAZ_TYPE_LOOKUP[hazard]
    return impf
        


def get_hazard(haz_type, country_iso3alpha, scenario, ref_year):
    client = Client()
    if haz_type == 'tropical_cyclone':
        return client.get_hazard(haz_type, properties={'country_iso3alpha': country_iso3alpha, 'climate_scenario': scenario, 'ref_year': str(ref_year)})
    elif haz_type == 'river_flood':
        year_range_midpoint = round(ref_year/20) * 20
        year_range = str(year_range_midpoint - 10) + '_' + str(year_range_midpoint + 10)
        return client.get_hazard(haz_type, properties={'country_iso3alpha': country_iso3alpha, 'climate_scenario': scenario, 'year_range': year_range})

