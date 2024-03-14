import pandas as pd
import geopandas as gpd
import numpy as np

from shapely import vectorized
from tqdm import tqdm
import shapely.vectorized

_SHAPEFILE = gpd.read_file(r"C:\Users\AndreaAngelidou\Documents\nccs-correntics\forestry\TM_WORLD_BORDERS-0.3.shp")

def get_country_vectorized_ISO_2(coordinates):
    iso3_codes = np.empty(len(coordinates), dtype=object)
    for idx, country in tqdm(_SHAPEFILE.iterrows(), total=len(_SHAPEFILE), desc='Processing countries'):
        xs = np.array([point.x for point in coordinates])
        ys = np.array([point.y for point in coordinates])
        lbls = shapely.vectorized.contains(country.geometry, xs, ys)
        iso3_codes[lbls] = country['ISO3']  # Assuming 'iso3' is the column with ISO3 codes in your _SHAPEFILE
    return iso3_codes.tolist()

subscores = ["Subscore_energy", "Subscore_water", "Subscore_waste"]

for subscore in subscores:
    input_file = f"data/{subscore}_stp2.h5"
    output_file = f"data/{subscore}_ISO3.h5" # first output for region_id assignment
    colum_latitude = 'latitude'
    column_longitude = 'longitude'

    df = pd.read_hdf(input_file)

    # Convert string values in latitude and longitude columns
    df[colum_latitude] = pd.to_numeric(df[colum_latitude], errors='coerce')
    df[column_longitude] = pd.to_numeric(df[column_longitude], errors='coerce')

    # Create a GeoDataFrame from the latitude and longitude columns
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[column_longitude], df[colum_latitude]))

    # # Skip rows where latitude or longitude is NaN
    # gdf = gdf.dropna(subset=[column_longitude, colum_latitude])
    #

    # Apply the vectorized function to the entire GeoDataFrame
    gdf['region_id'] = get_country_vectorized_ISO_2(gdf.geometry)

    gdf = gdf.dropna()

    df = pd.DataFrame(gdf.drop(columns='geometry'))
    df.to_hdf(output_file, key="data", mode='w')