import xarray as xr
import pandas as pd
from io import StringIO

"""
The hdf5 also needs a package called tables, which is why it is best to also run this code in the
virtual environment .venv (Python 3.10 (nccs-correntics)


Additionally, had to remove the two top lines within the header of the txt file of the raw data
"""

year = 2011 #what is the year of the emissions

# Read the text file into a string
with open(f"C:/github/nccs-correntics/manufacturing/manufacturing_general_exposure/raw_data_EDGAR/EDGARv6.1_NOx_{year}_TOTALS.txt", 'r') as file:
    data = file.read()

# Parse data into a DataFrame
df = pd.read_csv(StringIO(data), delimiter=';')

# Create the final DataFrame with desired structure
df_final = pd.DataFrame({
    'latitude': df['lat'],
    'longitude': df['lon'],
    'emi_nox': df[f'emission {year} (tons)']
})

#Count the number of rows that have a value of exacetly zero
num_rows_with_zero = len(df_final[df_final['emi_nox'] == 0])

#Insert a threshold of NOx emsions to account for manufacturing activities only
#In Tobler et al. 2018, 100t per year were used
# Filter rows where emi_nox >= 100
filtered_df = df_final[df_final['emi_nox'] >= 100]


hdf_filename = f"C:/github/nccs-correntics/manufacturing/manufacturing_general_exposure/intermediate_data_EDGAR/global_noxemissions_{year}_above_100t_0.1deg.h5" #high res

filtered_df.to_hdf(hdf_filename, key='data', mode='w')