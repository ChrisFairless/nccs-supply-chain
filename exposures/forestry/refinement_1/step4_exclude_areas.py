import geopandas as gpd
import pandas as pd
# from climada_petals.util.constants import DICT_GEOFABRIK
import glob
import fiona
from dict_step5 import DICT # new disctionary imported from forestry/step5_exposures_forestry.py given that RUS iso3 code is different in DICT_GEOFABRIK and DICT
import json
from shapely.geometry import shape


def read_geojson_manually(file_path):
    with open(file_path) as f:
        ds = json.load(f)

    data_fields = []
    geometry = []
    for feature in ds["features"]:
        properties = feature['properties']
        geometry.append(shape(feature["geometry"]))
        data_fields.append(properties)

    df = gpd.GeoDataFrame(
        data=data_fields,
        geometry=geometry
    )

    df.crs = 'EPSG:4326'

    return df

directory = "data"

colum_latitude = 'latitude'
column_longitude = 'longitude'
df = pd.read_hdf(r"C:\Users\AndreaAngelidou\Documents\nccs-correntics\forestry\data\forest_exp_region_final_v3.h5") ## use file from step 2 where we selected the 8 forest class areas and assigned region_id
df[colum_latitude] = pd.to_numeric(df[colum_latitude], errors='coerce')
df[column_longitude] = pd.to_numeric(df[column_longitude], errors='coerce')
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[column_longitude], df[colum_latitude]))
gdf.crs = 'EPSG:4326'

dict_list = list(DICT.keys())
countries = list(df["region_id"].unique())
dfs = []

for iso3 in countries:
    if iso3 in dict_list:
        file = f'{directory}/{DICT[iso3][1]}-nat-prot.geojson'
        try:
            # Let's first try to read this with fiona, this might break due to unclear reasons
            ds = gpd.read_file(file)
        except fiona.errors.DriverError:
            # let's read the geojson manually using shapely
            ds = read_geojson_manually(file)

        gdf_area = gdf.loc[gdf['region_id'] == iso3]

        joined_gdf = gpd.sjoin(gdf_area, ds, how='left', predicate="within")

        del gdf_area

        # Filter rows where points are not within multipolygons i.e. exclude rows which are natural and protected areas
        filtered_gdf = joined_gdf[joined_gdf['index_right'].isna()]

        # Drop unnecessary columns from the result
        filtered_gdf = filtered_gdf[df.columns]

        dfs.append(filtered_gdf)

    else:
        gdf_area = gdf.loc[gdf['region_id'] == iso3]

        gdf_area = gdf_area[df.columns] # drop geometry column in order to save .h5 file

        dfs.append(gdf_area)
        del gdf_area

dfs = pd.concat(dfs)
dfs.to_hdf(f'{directory}/forest_exp_osm_step4.h5', key="data", mode='w') # final file to use in step 5





