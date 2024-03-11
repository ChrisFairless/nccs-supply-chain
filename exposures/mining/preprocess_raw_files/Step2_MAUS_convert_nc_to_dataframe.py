import xarray as xr
import pandas as pd

"""
The hdf5 also needs a package called tables, which is why it is best to also run this code in the
virtual environment .venv
"""

# file = xr.open_dataset(r"C:\github\nccs-correntics\mining\intermediate_data_MAUS\global_miningarea_v2_5arcminute_converted.nc") #low res
file = xr.open_dataset(r"C:\github\nccs-correntics\mining\intermediate_data_MAUS\global_miningarea_v2_30arcsecond_converted.nc") #high res

#rename the variable
file = file.rename({"vale": "area"})
#drop unneccesary cooridnates and variables
file=file.sel(band=1).drop("band")
file=file.drop("spatial_ref")
#rename the coordinates
file = file.rename({"y": "latitude", "x": "longitude"})
#This process takes quite a while and blows up the memory if high resolution
df = file.to_dataframe().reset_index()
df = df.dropna()

#Count the number of rows that have a value of exacetly zero
num_rows_with_zero = len(df[df['area'] == 0])

#Take only the values that are not zero
df_filtered = df[df['area'] != 0]


# hdf_filename = r"C:\github\nccs-correntics\mining\intermediate_data_MAUS\global_miningarea_v2_5arcminute_converted.h5" #low res
hdf_filename = r"C:\github\nccs-correntics\mining\intermediate_data_MAUS\global_miningarea_30arcsecond_converted.h5" #high res

df_filtered.to_hdf(hdf_filename, key='data', mode='w')
