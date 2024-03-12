import pandas as pd
import geopandas as gpd
import numpy as np
import h5py
from shapely import vectorized
import shapely.vectorized
from tqdm import tqdm
import os

from exposures.utils import root_dir

# Get the root directory
project_root = root_dir()

_SHAPEFILE = gpd.read_file(f"{project_root}/exposures/mining/core/TM_WORLD_BORDERS-0.3.shp")

year = 2011
input_file = f"{project_root}/exposures/manufacturing/manufacturing_general_exposure/intermediate_data_EDGAR/global_noxemissions_{year}_above_100t_0.1deg.h5"
output_file = f"{project_root}/exposures/manufacturing/manufacturing_general_exposure/intermediate_data_EDGAR/global_noxemissions_{year}_above_100t_0.1deg_ISO3.h5"

column_latitude = 'latitude'
column_longitude = 'longitude'

df = pd.read_hdf(input_file)

# Convert string values in latitude and longitude columns
df[column_latitude] = pd.to_numeric(df[column_latitude], errors='coerce')
df[column_longitude] = pd.to_numeric(df[column_longitude], errors='coerce')

# Cretae a GeoDataFrame from the latitude and longitude columns
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[column_longitude], df[column_latitude]))

# Skip rows where latitude or longitude is NAN
gdf = gdf.dropna(subset=[column_longitude, column_latitude])


# For 3 million rows it took about 2.5 hours
def get_country_vectorized_ISO_2(coordinates):
    iso3_codes = np.empty(len(coordinates), dtype=object)
    for idx, country in tqdm(_SHAPEFILE.iterrows(), total=len(_SHAPEFILE), desc='Processing countries'):
        xs = np.array([point.x for point in coordinates])
        ys = np.array([point.y for point in coordinates])
        lbls = shapely.vectorized.contains(country.geometry, xs, ys)
        iso3_codes[lbls] = country['ISO3']  # Assuming 'iso3 is the column wth ISO3 codes in the _SHAPEFILE
    return iso3_codes.tolist()


# Apply the vectorized function to the entire GeoDataFrame, #For 3 million rows it took about 2.5 hours, took roughly 5 minutes
gdf['region_id'] = get_country_vectorized_ISO_2(gdf.geometry)

## Drop the 'geometry' colum
df1 = pd.DataFrame(gdf.drop(columns='geometry'))

##Count the number of rows where no country could be assigned
print("Number of rows where no country could be assigned: ", df1["region_id"].isnull().sum())

# Drop those columns
df2 = df1.dropna(subset=['region_id'])
df2.to_hdf(output_file, key='data', mode='w')
