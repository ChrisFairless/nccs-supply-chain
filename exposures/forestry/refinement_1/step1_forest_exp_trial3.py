import xarray as xr
from dask.diagnostics import ProgressBar
import pandas as pd

# Land cover file downloaded from Copernicus Climate Data Store
file = xr.open_dataset(r"C:\Users\AndreaAngelidou\climada\data\C3S-LC-L4-LCCS-Map-300m-P1Y-2020-v2.1.1.nc")

file = file.sel(time='2020-01-01T00:00:00').drop("time")
file = file.rename({"lccs_class": "value"})
file = file["value"]
file = file.chunk(chunks={'lat': 1000, 'lon': 1000})

# select only the 8 classes
forest = (50 <= file) & (file <= 90) & (file != 62) & (file != 72) & (file != 82)

forest = forest.rename({"lat": "latitude", "lon": "longitude"})

# change resolution from 300m to 3km
forest = forest.sel(latitude=slice(89,-89, 10), longitude=slice(-180,180, 10))

with ProgressBar():
    forest = forest.compute()

# mask dataset
forest_2 = forest / forest
forest_2.to_dataset(name="value").to_netcdf("f_exp_new.nc")
df = forest_2.to_dataframe(name='value').reset_index()
# keep only values with 1
df_2 = df.dropna()

hdf_filename = 'data/forest_exp_v3.h5'
df_2.to_hdf(hdf_filename, key='data', mode='w')