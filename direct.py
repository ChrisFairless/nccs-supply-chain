import pycountry
import pandas as pd

from climada.util.api_client import Client
from climada.entity import ImpfTropCyclone, ImpactFuncSet
from climada.engine.impact_calc import ImpactCalc

HAZ_TYPE_LOOKUP = {
    'tropical_cyclone': 'TC',
    'river_flood': 'RF'
}


# Method to loop through configuration lists of and run an impact calculation for 
# each combination on the list
# Simple, but can be sped up and memory usage reduced
def nccs_direct_impacts_list_simple(hazard_list, sector_list, country_list, scenario, ref_year):
    return pd.DataFrame(
        dict(
            haz_type=haz_type,
            sector=sector,
            country=country,
            scenario=scenario,
            ref_year=ref_year,
            impact_eventset=nccs_direct_impacts_simple(haz_type, sector, country, scenario, ref_year)
        )
        for haz_type in hazard_list for sector in sector_list for country in country_list
    )

def nccs_direct_impacts_simple(haz_type, sector, country, scenario, ref_year):
    country_iso3alpha = pycountry.countries.get(name=country).alpha_3
    haz = get_hazard(haz_type, country_iso3alpha, scenario, ref_year)
    exp = get_sector_exposure(sector, country)
    impf_set = get_sector_impf_set(haz_type, sector, country)
    return ImpactCalc(exp, impf_set, haz).impact(save_mat=True)


def nccs_direct_impacts(hazard_list, sector_list, country_list, scenario):
    client = Client()

    country_iso3alpha_list = [pycountry.countries.get(name=country).alpha_3 for country in country_list]

    # all combinations of hazard, exposure and country
    analyses_hazards = [
        {
            "hazard": hazard,
            "country": country,
            "reg_id": i_country,
            "haz": client.get_hazard(hazard, properties={'country_iso3alpha': country, 'climate_scenario': scenario}),
        } 
        for i_country, country in enumerate(country_iso3alpha_list) for hazard in hazard_list
    ]

    # all exposures
    analyses_exposures = [
        {
            "sector": sector,
            "country": country,
            "reg_id": i_country,
            "exp": get_sector_exposure(sector, country),
        } 
        for i_country, country in enumerate(country_iso3alpha_list) for sector in sector_list
    ]

    for item in analyses_exposures:
        # Set region ID
        item['exp'].gdf['reg_id'] = item['reg_id']

    # generate impact functions
    analyses_impfs = [
        {
            "sector": sector,
            "country": country,
            "reg_id": i_country,
            "impf_set": get_sector_impf_set(hazard, sector, country)
        }
        for i_country, country in enumerate(country_iso3alpha_list) for sector in sector_list for hazard in hazard_list
    ]

    # Identify which hazards have matching centroids
    analyses_hazards['centroid_set_id'] = [
        np.which([
            np.all_equal(analyses_hazards[i, 'haz'].centroids.lat, analyses_hazards[j, 'haz'].centroids.lat)
            for j in range(i)
        ])[0]
        for i in range(analyses_hazards.shape[0])
    ]

    # And assign centroids to exposures accordingly
    for 

    analyses_hazards = pd.DataFrame(analyses_hazards)
    analyses_exposures = pd.DataFrame(analyses_exposures)
    analyses_impfs = pd.DataFrame(analyses_impfs).drop_duplicates()
    analyses_impfs['impf_id'] = np.arange(analyses_impfs.shape[0])

    analyses_all = analyses_exposures.join(analyses_hazards, on=['country', 'reg_id']).join(analyses_impfs, on=['country', 'reg_id', 'sector'])

    analyses_all['imp'] = [ImpactCalc(row['exp'], row['impf_set'], row['haz']) for row in tqdm(analyses_all.itertuples())]


    aggregation_dimensions = set()
    if not save_by_country:
        analyses.aggregate()
    if not save_by_hazard:
        aggregation_dimensions.add('hazard')
    if not save_by_sector:
        aggregation_dimensions.add('sector')
       



    exp_all = Exposures.concat(exp_list)

    # Calculate direct impacts to the USA due to TC
    imp_calc = ImpactCalc(exp_usa, impf_set, tc_usa)
    direct_impact_usa = imp_calc.impact()


def get_sector_exposure(sector, country):
    if sector == 'service':
        client = Client()
        exp = client.get_litpop(country)
        exp.gdf['value'] = exp.gdf['value'] # / 100

    # add more sectors
    return exp


def get_sector_impf_set(hazard, sector, country):
    return ImpactFuncSet([get_sector_impf(hazard, sector, country)])


def get_sector_impf(hazard, sector, country):
    # TODO: load regional impfs based on country and
    # sector-specific impfs when they'll be available
    impf = ImpfTropCyclone.from_emanuel_usa()
    impf.haz_type = HAZ_TYPE_LOOKUP[hazard]
    return impf


def get_hazard(haz_type, country_iso3alpha, scenario, ref_year):
    client = Client()
    if haz_type == 'tropical_cyclone':
        return client.get_hazard(haz_type, properties={'country_iso3alpha': country_iso3alpha, 
                                                       'climate_scenario': scenario, 'ref_year': str(ref_year)})
    elif haz_type == 'river_flood':
        year_range_midpoint = round(ref_year/20) * 20
        year_range = str(year_range_midpoint - 10) + '_' + str(year_range_midpoint + 10)
        return client.get_hazard(haz_type, properties={'country_iso3alpha': country_iso3alpha, 
                                                       'climate_scenario': scenario, 'year_range': year_range})