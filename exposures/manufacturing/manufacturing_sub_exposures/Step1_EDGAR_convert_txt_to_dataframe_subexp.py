import xarray as xr
import pandas as pd
from io import StringIO

"""
The hdf5 also needs a package called tables, which is why it is best to also run this code in the
virtual environment .venv (Python 3.10 (nccs-correntics)


Additionally, had to remove the two top lines within the header of the txt file of the raw data
"""
year = 2011
emission_threshold = 0 # Insert a threshold of NOx emissions to account for manufacturing activities only
emission_threshold_scaled = 100

# List of files to loop through
# files = {
#     'food_and_paper': f'EDGARv6.1_NOx_{year}_FOO_PAP.txt',
#     'refin_and_transform': f'EDGARv6.1_NOx_{year}_REF_TRF.txt',
#     'chemical_process':f'EDGARv6.1_NMVOC_{year}_CHE.txt',
#     'non_metallic_mineral': f'EDGARv6.1_PM10_{year}_NMM.txt',
#     'basic_metals':f'EDGARv6.1_CO_{year}_BASICMETALS_combined.txt',
#     'pharmaceutical':f'EDGARv6.1_NMVOC_{year}_CHE.txt',
#     'wood':f'EDGARv6.1_NOx_{year}_TOTALS.txt', #when changing this to something explicit, change threshold if
#     'rubber_and_plastic':f'EDGARv6.1_NOx_{year}_TOTALS.txt', #when changing this to something explicit, change threshold if
#     # Add more files as needed
# }
#
# #Adjust the substance according to the filename
# substances = {
#     'food_and_paper': 'NOx',
#     'refin_and_transform': 'NOx',
#     'chemical_process':'NMVOC',
#     'non_metallic_mineral':'PM10',
#     'basic_metals':'CO',
#     'pharmaceutical':'NMVOC',
#     'wood':'NOx',
#     'rubber_and_plastic':'NOx',
#     # Add more files as needed
# }

#run it only for one new file

files = {
    'wood':f'EDGARv6.1_NOx_{year}_TOTALS.txt',
    'rubber_and_plastic':f'EDGARv6.1_NOx_{year}_TOTALS.txt',
}

substances = {
    'wood':'NOx',
    'rubber_and_plastic':'NOx',
}

for variable, filename in files.items():
    # Read the text file into a string
    with open(f"C:/github/nccs-correntics/manufacturing/manufacturing_sub_exposures/raw_data_EDGAR/{filename}", 'r') as file:
        data = file.read()
        substance=substances[variable]

    # Parse data into a DataFrame
    df = pd.read_csv(StringIO(data), delimiter=';')

    # Create the final DataFrame with desired structure
    df_final = pd.DataFrame({
        'latitude': df['lat'],
        'longitude': df['lon'],
        'emission_t': df[f'emission {year} (tons)']
    })
    print(variable, "filtered_df:", df_final)

    # Count the number of rows that have a value of exactly zero
    num_rows_with_zero = len(df_final[df_final['emission_t'] == 0])
    print(variable, "num_rows_with_zero:", num_rows_with_zero)

    # Filter rows where emi_nox >= emission threshold
    #use a different threshold for exposures that come from the large set and not a sector-specific
    if variable == 'wood' or variable == 'rubber_and_plastic':
        emission_threshold = emission_threshold_scaled
        print (f'emission threshold was set to {emission_threshold_scaled} as not a spector specific exposure for: {variable}')
    filtered_df = df_final[df_final['emission_t'] >= emission_threshold]
    print(variable, f"filtered_df>{emission_threshold}t:", filtered_df)

    # Define HDF filename based on variable and year
    hdf_filename = f"C:/github/nccs-correntics/manufacturing/manufacturing_sub_exposures/intermediate_data_EDGAR/{variable}_{substance}_emissions_{year}_above_{emission_threshold}t_0.1deg.h5"

    # Save to HDF file
    filtered_df.to_hdf(hdf_filename, key='data', mode='w')

    print(f"Processed {variable} data and saved to {hdf_filename}")