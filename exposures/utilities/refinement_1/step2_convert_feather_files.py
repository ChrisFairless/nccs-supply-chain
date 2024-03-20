import pandas as pd
import geopandas as gpd
from shapely import wkb


# example for one file
#TODO change and save the raw data files also somewhere?
df = pd.read_feather(r"C:\Users\AndreaAngelidou\Documents\nccs-correntics\utilities\data\max_method\utilities_exposure_all.feather")
gdf = gpd.GeoDataFrame(df)
gdf['geometry'] = gdf['geometry'].apply(lambda x: wkb.loads(x, hex=True))
gdf = gdf.set_geometry("geometry")

# STEP1: get the lat, lon from polygon and save each subscore individually
lat_points = []
lon_points = []
# Iterate through each row in the GeoDataFrame
for index, row in gdf.iterrows():
    # Get the centroid of the polygon in EPSG 4326
    centroid = row['geometry'].centroid
    # Append latitude and longitude of the centroid
    lat_points.append(centroid.y)
    lon_points.append(centroid.x)

lat_points = pd.Series(lat_points, name="latitude")
lon_points = pd.Series(lon_points, name="longitude")

subscores = ["Subscore_energy", "Subscore_water", "Subscore_waste"]

for subscore in subscores:

    df = gdf[subscore]

    df = pd.concat([df, lat_points, lon_points], keys=[subscore, "latitude", "longitude"], axis=1)

    df = df[df[subscore] != 0].reset_index(drop=True) # remove 0 values from subscore

    df.to_hdf(f"data/{subscore}_stp2.h5", key="data", mode='w')