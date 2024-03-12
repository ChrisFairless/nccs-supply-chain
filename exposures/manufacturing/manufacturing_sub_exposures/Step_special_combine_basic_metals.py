import xarray as xr
import pandas as pd
import geopandas as gpd
from io import StringIO
from exposures.utils import root_dir

# Get the root directory
project_root = root_dir()

year = 2011

with open(f"{project_root}/manufacturing/manufacturing_sub_exposures/raw_data_EDGAR/EDGARv6.1_CO_2011_IRO.txt",
          'r') as file:
    IRO_data = file.read()

with open(f"{project_root}/manufacturing/manufacturing_sub_exposures/raw_data_EDGAR/EDGARv6.1_CO_2011_NFE.txt",
          'r') as file:
    NFE_data = file.read()

# Parse data into a DataFrame
df_IRO = pd.read_csv(StringIO(IRO_data), delimiter=';')
df_NFE = pd.read_csv(StringIO(NFE_data), delimiter=';')

# Concatenate the DataFrames
concatenated_df = pd.concat([df_IRO, df_NFE], ignore_index=True)

# Create a new column with the combined lon and lat
concatenated_df['lon_lat_combined'] = concatenated_df.apply(lambda row: f"({row['lon']}, {row['lat']})", axis=1)

# Group by 'lon_lat_combined' and sum emissions
summed_df = concatenated_df.groupby('lon_lat_combined').agg({'emission 2011 (tons)': 'sum', 'lat': 'first', 'lon': 'first'}).reset_index()

# Drop unnecessary columns
summed_df_final = summed_df.drop(['lon_lat_combined'], axis=1)


# Save the file again as a text file, so be consistent with the whole approach
output_file_path = f"{project_root}/manufacturing/manufacturing_sub_exposures/raw_data_EDGAR/EDGARv6.1_CO_2011_BASICMETALS_combined.txt"

# Save the DataFrame to a text file with semicolon as the delimiter
summed_df_final.to_csv(output_file_path, sep=';', index=False)

print(f"DataFrame saved to {output_file_path}")

"""Some check points"""
#count the occurence of unique values in the "lon_lat_combined colum
count_by_lon_lat_combined = concatenated_df['lon_lat_combined'].value_counts()
print ("unique values of lon_lat_combined values:", count_by_lon_lat_combined)
num_duplicates = concatenated_df['lon_lat_combined'].duplicated().sum()
print(f"Number of duplicates in lon_lat_combined column: {num_duplicates}")

#Sort the duplicates to see them explicitely
duplicate_mask = concatenated_df.duplicated(subset='lon_lat_combined', keep=False)
duplicate_rows = concatenated_df[duplicate_mask]
sorted_duplicate_rows = duplicate_rows.sort_values(by='lon_lat_combined')
print("Sorted Duplicate Rows:")
print(sorted_duplicate_rows)

#get the for an exllicti lat lon combination the final row
# Replace (-0.1, 42.8) with the lon_lat_combined value you're interested in
target_lon_lat_combined = '(-46.4, -23.4)'
row_for_target_value = summed_gdf[summed_gdf['lon_lat_combined'] == target_lon_lat_combined]
emission_for_target_value = row_for_target_value['emission 2011 (tons)'].values
print(f"Emission for lon_lat_combined {target_lon_lat_combined}: {emission_for_target_value}")


