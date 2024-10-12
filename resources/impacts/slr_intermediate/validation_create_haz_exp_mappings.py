# This script is unused in the final modelling chain
# However its method for mapping between the Exposure datasets and the SLR data is more accurate than the (much faster) 
# method used in the final script. I recommend using it as a way to validate that all grid cells are successfully 
# matched, especially in larger countries where small errors in grid spacing definitions might add up to large errors
# across large distances

import sys
sys.path.append('../../..')

import pandas as pd
import numpy as np
import os
from pathlib import Path
from climada.hazard import Hazard, Centroids
from climada.entity import Exposures
import rioxarray as rxr
import itertools
import pycountry
from functools import reduce, partial
from climada.util.constants import DEF_CRS
import climada.util.coordinates as u_coord
import traceback
import pathos as pa

from nccs.pipeline.direct.direct import get_sector_exposure

aqueduct_metadata_path = Path('.', 'data', 'aqueduct_download_metadata.csv')
country_bounding_box_path = Path('.', 'data', 'country_bounding_boxes.csv')
exposure_metadata_path = Path('.', 'data', 'exposure_metadata.csv')

mapping_metadata_outpath = Path('.', 'data', 'hazard_exposure_mapping_metadata.csv')

output_dir = Path('.', 'data', 'deleteme_results')
hazmap_dir = Path('.', 'data', 'deleteme_intermediate')
# aqueduct_metadata_path = Path('.', 'resources', 'impacts', 'slr_intermediate', 'data', 'aqueduct_download_metadata.csv')
# country_bounding_box_path = Path('.', 'resources', 'impacts', 'slr_intermediate', 'data', 'country_bounding_boxes.csv')
# output_dir = Path('.', 'resources', 'impacts', 'slr_intermediate', 'data', 'results')

aqueduct_metadata = pd.read_csv(aqueduct_metadata_path)
country_bounding_boxes = pd.read_csv(country_bounding_box_path)
exposure_metadata = pd.read_csv(exposure_metadata_path)

sector_list = ["agriculture", "forestry", "mining", "manufacturing", "service", "energy", "water", "waste",
                "basic_metals", "pharmaceutical", "food", "wood", "chemical", "rubber_and_plastic",
                "non_metallic_mineral", "refin_and_transform"]
# sector_list = ["mining", "manufacturing"]
# sector_list = ['manufacturing', 'pharmaceutical']

n_cpus = pa.helpers.cpu_count() - 1
# n_cpus = 4

assert(os.path.exists(output_dir))
assert(os.path.exists(hazmap_dir))

year_rank_map = {'hist': 0, '2020': 1, '2050': 2, '2080': 3}
scenario_rank_map = {'historical': 0, 'rcp4p5': 1, 'rcp8p5': 2}
aqueduct_metadata['year_rank'] = [year_rank_map[y] for y in aqueduct_metadata['year']]
aqueduct_metadata['scenario_rank'] = [scenario_rank_map[s] for s in aqueduct_metadata['scenario']]
aqueduct_metadata = aqueduct_metadata.sort_values(['rp', 'scenario_rank', 'year_rank'], ascending=False)
assert(len(np.unique(aqueduct_metadata['subsidence'])) == 1)  # ranking doesn't include this yet

aqueduct_metadata = aqueduct_metadata[aqueduct_metadata['perc'] != 50]  # not ready for this yet

exposure_metadata = exposure_metadata[~pd.isna(exposure_metadata['res'])]
exposure_metadata = exposure_metadata.sort_values(['country', 'sector']).set_index(['country', 'sector'])
exposure_metadata['res'] = np.round(exposure_metadata['res'], 5)

mapping_df = pd.DataFrame(columns=['country', 'sector', 'mapping_filename']).set_index(['country', 'sector'])


max_slr_metadata = aqueduct_metadata.iloc[0]
slr = rxr.open_rasterio(max_slr_metadata['local_path'])

def combine_transforms(transform_list):
    transform_list = [eval(t) if isinstance(t, str) else t for t in transform_list]
    xres = transform_list[0][0]
    yres = transform_list[0][4]
    assert(np.min(np.abs([t[0] - xres for t in transform_list])) < 0.0001)
    assert(np.min(np.abs([t[4] - yres for t in transform_list])) < 0.0001)
    xmin = np.min([t[2] for t in transform_list])
    ymin = np.min([t[5] for t in transform_list])
    out = transform_list[0]
    out[2] = xmin
    out[5] = ymin
    return out

def get_exposure_mappings(haz_df, transform):
    # Partially stolen from climada.util.coordinates.match_grid_points
    x = haz_df.index.get_level_values('lon')
    y = haz_df.index.get_level_values('lat')
    xres, _, xmin, _, yres, ymin = transform[:6]
    xmin, ymin = xmin + 0.5 * xres, ymin + 0.5 * yres
    x_i = np.round((x - xmin) / xres).astype(int)
    y_i = np.round((y - ymin) / yres).astype(int)
    lons = xmin + (x_i * xres)
    lats = ymin + (y_i * yres)
    return pd.DataFrame(dict(
        haz_lat = y,
        haz_lon = x,
        exp_lat = lats,
        exp_lon = lons
    ))


for _, crow in country_bounding_boxes.iterrows():
    country = crow['country']
    print(f"Working on country {country}")
    country_iso3num = pycountry.countries.get(name=crow['country']).numeric

    country_exposures_df = exposure_metadata.loc[country]
    if country_exposures_df.shape[0] == 0:
        print("... no exposures for this country. Skipping.")
        continue

    subset_lons = slr.x[np.multiply(slr.x >= crow['lon_min'], slr.x <= crow['lon_max'])]
    subset_lats = slr.y[np.multiply(slr.y >= crow['lat_min'], slr.y <= crow['lat_max'])]
    subset = slr.loc[1, subset_lats, subset_lons]
    haz_df = subset.to_pandas()
    haz_df = pd.melt(haz_df, var_name = 'x', value_name='depth', ignore_index=False)
    haz_df = haz_df[haz_df['depth'] != slr._FillValue]
    haz_df = haz_df[haz_df['depth'] > 0]
    haz_df = haz_df.reset_index().rename(columns={'x': 'lon', 'y': 'lat'})
    haz_df['lat'] = np.round(haz_df['lat'], 6)  # For index matching later
    haz_df['lon'] = np.round(haz_df['lon'], 6)
    haz_df.set_index(['lat', 'lon'], inplace=True)

    if haz_df.shape[0] == 0:
        print(f'... no hazard near to exposures. No mapping for {country}')
        continue

    for res in np.unique(country_exposures_df['res']):
        print(f'... finding mappings for resolution {res}')
        res_exposures_df = country_exposures_df[country_exposures_df['res'] == res]
        this_sectors = list(res_exposures_df.index.get_level_values('sector'))
        print(f'   ... sectors: {this_sectors}')
        transform = combine_transforms(res_exposures_df['transform'])
        mapping = get_exposure_mappings(haz_df, transform)
        mapping_filename = f'hazmap_{country}_{this_sectors[0]}.csv'
        mapping.to_csv(Path(hazmap_dir, mapping_filename))
        for i_sector in this_sectors:
            mapping_df.loc[(i_sector, country), 'mapping_filename'] = mapping_filename

mapping_df.to_csv(mapping_metadata_outpath)




