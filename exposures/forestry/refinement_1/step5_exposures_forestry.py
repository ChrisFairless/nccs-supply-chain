import xarray
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import pycountry

from climada.entity import Exposures
import climada.util.coordinates as u_coord
from climada_petals.engine import SupplyChain

import logging

LOGGER = logging.getLogger()

def get_forestry_exp_new_2(
        countries=None,
        mriot_type='WIOD16',
        mriot_year=2011, # 2011 year used for WIOD16, update as needed
        repr_sectors='Forestry and logging'):

    glob_prod, repr_sectors, IO_countries = get_prod_secs(mriot_type, mriot_year, repr_sectors)

    ## option 1: distribute ROW production value equally (implemented as first approach)
    # n_total = 195
    # ROW_factor = (1 / (n_total - (len(set(r[0] for r in glob_prod.axes[0])) - 1)))
    # Row_country_production = ((glob_prod.loc["ROW"].loc[repr_sectors].sum()).values[0] * ROW_factor)

    ## option 2: distribute ROW production value according to GDP (implemented as second approach)
    ROW_gdp_lookup = get_ROW_factor_GDP(mriot_year, IO_countries, countries)

    cnt_dfs = []

    data = pd.read_hdf("data/forest_exp_osm_step4.h5") # file from step 4 excluding national parks and protected areas

    for iso3_cnt in countries:

        cnt_df = data.loc[data['region_id'] == iso3_cnt]

        try:
            cnt_df['value'] = glob_prod.loc[iso3_cnt].loc[repr_sectors].sum().values[0] / len(cnt_df)
        except KeyError:
            LOGGER.warning('You are simulating a country for which there are no production data in the chosen IOT')
            # code under option 1:
            # cnt_df["value"] = Row_country_production / len(cnt_df) # potential update to be scaled with GDP

            # code under option 2:
            try:
                ROW_gdp_factor = ROW_gdp_lookup.loc[ROW_gdp_lookup['Country Code'] == iso3_cnt, 'Normalized_GDP'].values[0]
                ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_gdp_factor)
                cnt_df['value'] = ROW_country_production / len(cnt_df)
            except:
                print(f"For the country {iso3_cnt} there is no GDP value available, 0 value is assigned")
                ROW_gdp_factor = 0
                ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_gdp_factor)
                cnt_df['value'] = ROW_country_production / len(cnt_df)

        cnt_dfs.append(cnt_df)

    exp = Exposures(pd.concat(cnt_dfs).reset_index(drop=True))
    exp.set_geometry_points()

    return exp


def get_prod_secs(mriot_type, mriot_year, repr_sectors):
    mriot = SupplyChain.from_mriot(mriot_type=mriot_type,
                                   mriot_year=mriot_year).mriot

    if isinstance(repr_sectors, (range, np.ndarray)):
        repr_sectors = mriot.get_sectors()[repr_sectors].tolist()

    elif isinstance(repr_sectors, str):
        repr_sectors = [repr_sectors]

    return mriot.x, repr_sectors, mriot.get_regions()

def get_ROW_factor_GDP(mriot_year, IO_countries, countries):
    IO_countries = IO_countries

    #load the GDP of counries
    gdp_worldbank = pd.read_csv('GDP_Worldbank_modified_without_regions.csv')

    # Select only the specified year column and filter rows based on the 'Country Code'
    ROW_gdp_worldbank = gdp_worldbank[['Country Code', str(mriot_year)]][~gdp_worldbank['Country Code'].isin(IO_countries)]
    # Assuming ROW_gdp_worldbank is your DataFrame and country is your list of countries
    filtered_gdp_worldbank = ROW_gdp_worldbank[ROW_gdp_worldbank['Country Code'].isin(countries)]

    ROW_total_GDP = filtered_gdp_worldbank[str(mriot_year)].sum()
    # Create a new column with normalized GDP values
    ROW_gdp_worldbank['Normalized_GDP'] = ROW_gdp_worldbank[str(mriot_year)] / ROW_total_GDP

    return ROW_gdp_worldbank


data = pd.read_hdf("data/forest_exp_osm_step4.h5") # file from step 4 excluding national parks and protected areas
countries = data["region_id"].unique().tolist()
countries.sort()
del data

# apply function that alters the value using MRIO
exp = get_forestry_exp_new_2(
    countries=countries,
    mriot_type='WIOD16',
    mriot_year=2011,
    repr_sectors='Forestry and logging')

df = exp.gdf.drop(columns='geometry')

df.to_hdf("data/forestry_values_MRIO_avg(GDP).h5", key="data", mode='w') # final file to be used in CLIMADA NCCS project
