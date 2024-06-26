import pandas as pd
import geopandas as gpd
import numpy as np
from lonlat_to_country import get_country_vectorized_name , get_country_vectorized_ISO, get_country
import h5py
from shapely import vectorized
from tqdm import tqdm
import shapely.vectorized

# shapefile used for region id assignment
_SHAPEFILE = gpd.read_file("TM_WORLD_BORDERS-0.3.shp")

input_file = "data/forest_exp_v3.h5" # file with forest data converted from nc to h5
output_file = "data/forest_exp_region_final_v3.h5" # first output for region_id assignment
colum_latitude = 'latitude'
column_longitude = 'longitude'

df = pd.read_hdf(input_file)

# Convert string values in latitude and longitude columns
df[colum_latitude] = pd.to_numeric(df[colum_latitude], errors='coerce')
df[column_longitude] = pd.to_numeric(df[column_longitude], errors='coerce')

# Create a GeoDataFrame from the latitude and longitude columns
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[column_longitude], df[colum_latitude]))

# Skip rows where latitude or longitude is NaN
gdf = gdf.dropna(subset=[column_longitude, colum_latitude])

def get_country_vectorized_ISO_2(coordinates):
    iso3_codes = np.empty(len(coordinates), dtype=object)
    for idx, country in tqdm(_SHAPEFILE.iterrows(), total=len(_SHAPEFILE), desc='Processing countries'):
        xs = np.array([point.x for point in coordinates])
        ys = np.array([point.y for point in coordinates])
        lbls = shapely.vectorized.contains(country.geometry, xs, ys)
        iso3_codes[lbls] = country['ISO3']  # Assuming 'iso3' is the column with ISO3 codes in your _SHAPEFILE
    return iso3_codes.tolist()


# Apply the vectorized function to the entire GeoDataFrame
gdf['region_id'] = get_country_vectorized_ISO_2(gdf.geometry)

# # Drop the 'geometry' column
df = pd.DataFrame(gdf.drop(columns='geometry'))
df["value"] = 1 ## change value to just 1 # this is not necessary as the value changes to step 5
# # Drop rows with NaN values on region_id
df = df.dropna()

df.to_hdf(output_file, key="data", mode='w')

