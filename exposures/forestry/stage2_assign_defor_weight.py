import pandas as pd
import geopandas as gpd
import numpy as np

def assign_geom(df):
    colum_latitude = 'latitude'
    column_longitude = 'longitude'

    # Convert string values in latitude and longitude columns
    df[colum_latitude] = pd.to_numeric(df[colum_latitude], errors='coerce')
    df[column_longitude] = pd.to_numeric(df[column_longitude], errors='coerce')

    # Create a GeoDataFrame from the latitude and longitude columns
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[column_longitude], df[colum_latitude]))

    return gdf

forest = pd.read_hdf("data/forest_exp_osm_step4.h5")
deforestation = pd.read_hdf("data/deforestation.h5")

forest = assign_geom(forest)
deforestation = assign_geom(deforestation)

joined = gpd.sjoin_nearest(forest, deforestation, how="left", max_distance=0.03, distance_col="distance_diff")
joined = joined.sort_values(by='distance_diff').drop_duplicates(subset='geometry', keep='first')

joined["weight"] = 0
joined['weight'] = np.where(joined['value_right'] == 1, 2, 1) # for sensitivity analysis change weight from 2 to 10

joined = joined[['latitude_left', 'longitude_left', 'value_left', 'region_id', 'weight']]
joined = joined.rename(columns={'latitude_left': 'latitude', 'longitude_left': 'longitude', 'value_left': 'value'})


joined["weight_norm"] = 0
def weight_calc(df):
    a = len(df.loc[df['weight'] == 2]) # for sensitivity analysis change weight from 2 to 10
    b = len(df.loc[df['weight'] == 1])

    y = len(df) / (2*a + b) # for sensitivity analysis change weight from 2 to 10
    x = 2 * y

    return x, y

cnt_dfs = []
countries = joined["region_id"].unique().tolist()

for iso3 in countries:

    cnt_df = joined.loc[joined['region_id'] == iso3]
    x, y = weight_calc(cnt_df)

    cnt_df['weight_norm'] = np.where(cnt_df['weight'] == 2, x, y)

    cnt_dfs.append(cnt_df)

cnt_dfs = pd.concat(cnt_dfs).reset_index(drop=True)

cnt_dfs.to_hdf("data/forest_exp_osm_defor(v2).h5", key="data", mode='w') # final file to use in step 5.2

