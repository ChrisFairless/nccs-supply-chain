import numpy as np
import h5py
from shapely import vectorized
import shapely.vectorized
from tqdm import tqdm
import geopandas as gpd
import pandas as pd
import os

_SHAPEFILE = gpd.read_file(r"C:/github/nccs-correntics/mining/preprocess_raw_files/TM_WORLD_BORDERS-0.3.shp")

year = 2011
emission_threshold = 0 # Insert a threshold of NOx emissions to account for manufacturing activities only
emission_threshold_scaled = 100 # Insert a threshold of NOx emissions to account for manufacturing activities only


#Chnage substance in filename if another one should be picked
# files = {
#     'food_and_paper': f'food_and_paper_NOx_emissions_{year}_above_{emission_threshold}t_0.1deg',
#     'refin_and_transform': f'refin_and_transform_NOx_emissions_{year}_above_{emission_threshold}t_0.1deg',
#     'chemical_process':f'chemical_process_NMVOC_emissions_{year}_above_{emission_threshold}t_0.1deg',
#     'non_metallic_mineral': f'non_metallic_mineral_PM10_emissions_{year}_above_{emission_threshold}t_0.1deg',
#     'basic_metals': f'basic_metals_CO_emissions_{year}_above_{emission_threshold}t_0.1deg',
#     'pharmaceutical':f'pharmaceutical_NMVOC_emissions_{year}_above_{emission_threshold}t_0.1deg',
#     'wood':f'wood_NOx_emissions_{year}_above_{emission_threshold_scaled}t_0.1deg',
#     'rubber_and_plastic':f'rubber_and_plastic_NOx_emissions_{year}_above_{emission_threshold_scaled}t_0.1deg'
#     # Add more files as needed
# }

#run it only for one new file
files = {
    'wood':f'wood_NOx_emissions_{year}_above_{emission_threshold_scaled}t_0.1deg',
    'rubber_and_plastic':f'rubber_and_plastic_NOx_emissions_{year}_above_{emission_threshold_scaled}t_0.1deg'
}

for variable, filename in files.items():
    input_file = f"intermediate_data_EDGAR/{filename}.h5"
    output_file = f"intermediate_data_EDGAR/{filename}_ISO3.h5"

    column_latitude = 'latitude'
    column_longitude = 'longitude'

    df = pd.read_hdf(input_file)

    # Convert string values in latitude and longitude columns
    df[column_latitude] = pd.to_numeric(df[column_latitude], errors='coerce')
    df[column_longitude] = pd.to_numeric(df[column_longitude], errors='coerce')

    # Create a GeoDataFrame from the latitude and longitude columns
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[column_longitude], df[column_latitude]))

    # Skip rows where latitude or longitude is NAN
    gdf = gdf.dropna(subset=[column_longitude, column_latitude])

    def get_country_vectorized_ISO_2(coordinates):
        iso3_codes = np.empty(len(coordinates), dtype=object)
        for idx, country in tqdm(_SHAPEFILE.iterrows(), total=len(_SHAPEFILE), desc='Processing countries'):
            xs = np.array([point.x for point in coordinates])
            ys = np.array([point.y for point in coordinates])
            lbls = shapely.vectorized.contains(country.geometry, xs, ys)
            iso3_codes[lbls] = country['ISO3']  # Assuming 'iso3 is the column with ISO3 codes in the _SHAPEFILE
        return iso3_codes.tolist()

    # Apply the vectorized functions to the entire GeoDataFrame
    gdf['region_id'] = get_country_vectorized_ISO_2(gdf.geometry)

    # Drop the 'geometry' column
    df1 = pd.DataFrame(gdf.drop(columns='geometry'))

    # Count the number of rows where no country could be assigned
    print(f"Number of rows where no country could be assigned for {variable}: ", df1["region_id"].isnull().sum())

    # Drop those columns
    df2 = df1.dropna(subset=['region_id'])

    print(f"Saved dataframe for {variable}:", df2)
    df2.to_hdf(output_file, key='data', mode='w')

    print(f"Processed {variable} data and saved to {output_file}")
