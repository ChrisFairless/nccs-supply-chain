import os

import numpy as np
import xarray as xr
import rioxarray
import dask
from dask.diagnostics import ProgressBar

# def reduce(x, axis=0):
#     x = x.flatten()
#     y = np.zeros_like(x)
#     y[np.where(x > 0)] = 1 # another way use da.where(x > 0, 1, 0)
#
#     y = y.sum()
#     y = y / len(x)
#
#     return y > 0.8


def open_concatenate_tifs(input_folder):
    tif_files = [os.path.join(input_folder, file) for file in os.listdir(input_folder) if file.endswith(".tif")]
    datasets = [
        rioxarray.open_rasterio(file, chunks={'y': 1000, 'x': 1000}).to_dataset(name="value").sel(band=1).drop_vars(
            ["band", "spatial_ref"]).rename({"x": "longitude", "y": "latitude"}) for file in tif_files]
    combined = xr.combine_by_coords(datasets)

    # select every 100th value change resolution from 30m to 3km
    combined = combined.sel(latitude=slice(89, -89, 100), longitude=slice(-180, 180, 100))
    #combined = combined.coarsen(latitude=100, longitude=100).max()

    # combined = combined.coarsen(latitude=100, longitude=100).reduce(reduce)


    # create as mask data
    combined = combined / combined
    combined = combined.astype("uint8")

    return combined


# Example usage:
input_folder = 'data/deforestation'  # Folder containing the input GeoTIFF files

combined = open_concatenate_tifs(input_folder)

with ProgressBar():
    combined = combined.compute()

df = combined.to_dataframe().reset_index()
df = df[df['value'] != 0]
df.to_hdf("data/deforestation.h5", key='data', mode='w')