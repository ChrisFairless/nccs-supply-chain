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

from exposures.utils import root_dir
from utils.s3client import upload_to_s3_bucket

# Get the root directory
project_root = root_dir()

def get_forestry_exp_new_2(
        countries=None,
        mriot_type='WIOD16',
        mriot_year=2011, # 2011 year used for WIOD16, update as needed
        repr_sectors='Forestry and logging'):

    glob_prod, repr_sectors, IO_countries = get_prod_secs(mriot_type, mriot_year, repr_sectors)


    ROW_WB_lookup = get_ROW_factor_WB_forestry(mriot_year, IO_countries, countries)

    cnt_dfs = []

    data = pd.read_hdf(f"{project_root}/exposures/forestry/refinement_1/intermediate_data/forest_exp_osm_defor(v2).h5") # file from step 4 excluding national parks and protected areas + deforestation

    for iso3_cnt in countries:

        cnt_df = data.loc[data['region_id'] == iso3_cnt]

        try:
            cnt_df['value'] = (glob_prod.loc[iso3_cnt].loc[repr_sectors].sum().values[0] / len(cnt_df)) * cnt_df['weight_norm']
        except KeyError:
            LOGGER.warning('You are simulating a country for which there are no production data in the chosen IOT')

            try:
                ROW_WB_factor = ROW_WB_lookup.loc[ROW_WB_lookup['Country Code'] == iso3_cnt, 'Normalized_WB'].values[0]
                ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_WB_factor)
                cnt_df['value'] = (ROW_country_production / len(cnt_df)) * cnt_df['weight_norm']
            except:
                print(f"For the country {iso3_cnt} there is no WB value available, 0 value is assigned")
                ROW_WB_factor = 0
                ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_WB_factor)
                cnt_df['value'] = (ROW_country_production / len(cnt_df)) * cnt_df['weight_norm']

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

def get_ROW_factor_WB_forestry(mriot_year, IO_countries, countries):
    IO_countries = IO_countries

    #load the forestry production of counries
    forestry_prod_WB = pd.read_csv(f'{project_root}/exposures/forestry/refinement_1/WorldBank_forestry_production.csv')

    # Select only the specified year column and filter rows based on the 'Country Code'
    ROW_forestry_prod_WB = forestry_prod_WB[['Country Code', str(mriot_year)]][~forestry_prod_WB['Country Code'].isin(IO_countries)]
    # Assuming ROW_forestry_prod_WB is your DataFrame and country is your list of countries
    filtered_forestry_prod_WB = ROW_forestry_prod_WB[ROW_forestry_prod_WB['Country Code'].isin(countries)]

    ROW_total_WB = filtered_forestry_prod_WB[str(mriot_year)].sum()
    # Create a new column with normalized WB values
    ROW_forestry_prod_WB['Normalized_WB'] = ROW_forestry_prod_WB[str(mriot_year)] / ROW_total_WB

    return ROW_forestry_prod_WB


data = pd.read_hdf(f"{project_root}/exposures/forestry/refinement_1/intermediate_data/forest_exp_osm_defor(v2).h5") # file from step 4 excluding national parks and protected areas + deforestation
countries = data["region_id"].unique().tolist()
countries.sort()
del data

# apply function that alters the value using MRIO
exp = get_forestry_exp_new_2(
    countries=countries,
    mriot_type='WIOD16',
    mriot_year=2011,
    repr_sectors='Forestry and logging')


# # Save a shape file to check it in QGIS
# df_shape = exp.gdf
# filename_shp = f"{project_root}/exposures/forestry/refinement_1/forestry_values_MRIO_avg(WB-v2).shp"
# s3_filename_shp = f"exposures/forestry/refinement_1/forestry_values_MRIO_avg(WB-v2).shp"
# df_shape.to_file(filename_shp,driver="ESRI Shapefile")
# # upload the file to the s3 Bucket
# upload_to_s3_bucket(filename_shp, s3_filename_shp)
# print(f"upload of {s3_filename_shp} to s3 bucket successful")


# Save final file to a climada available format h5
df = exp.gdf.drop(columns='geometry')
filename_h5 =f"{project_root}/exposures/forestry/refinement_1/forestry_values_MRIO_avg(WB-v2).h5"
s3_filename_h5 =f"exposures/forestry/refinement_1/forestry_values_MRIO_avg(WB-v2).h5"
df.to_hdf(filename_h5, key="data", mode='w') # final file to be used in CLIMADA NCCS project
# upload the file to the s3 Bucket
upload_to_s3_bucket(filename_h5, s3_filename_h5)
print(f"upload of {s3_filename_h5} to s3 bucket successful")

# Save individual country files #TODO save country splited files to S3 bucket
for region_id in df['region_id'].unique():
    subset_df = df[df['region_id'] == region_id]
    filename_country = f"{project_root}/exposures/forestry/refinement_1/country_split/forestry_values_MRIO_avg(WB-v2)_{region_id}.h5"
    s3_filename_country = f"exposures/forestry/refinement_1/country_split/forestry_values_MRIO_avg(WB-v2)_{region_id}.h5"
    subset_df.to_hdf(filename_country, key="data", mode="w")
    #upload the individual country files to s3 bucket
    upload_to_s3_bucket(filename_country, s3_filename_country)
    print(f"upload of {s3_filename_country} to s3 bucket successful")

