"""
This script is used to convert a tif into a nc file
"""
"""
Important, this script only works with the rioxarray package
To not interfere with any other projects, the rioxarray package is installed in the .venv
To switch to this .venv, click on the python interpreter Settings
Choose the project name | Python Interpreter. Click Add Interpreter, Select Add Local 
Interpreter. In the left-hand pane of the Add Python Interpreter dialog, select
Virtualenv Environment.
"""

import rioxarray
import xarray as xr

rds = rioxarray.open_rasterio(r"C:\github\nccs-correntics\mining\raw_data_MAUS\global_miningarea_v2_5arcminute.tif")
rds.to_dataset(name="vale").to_netcdf(r"C:\github\nccs-correntics\mining\intermediate_data_MAUS\global_miningarea_v2_5arcminute_converted.nc")
