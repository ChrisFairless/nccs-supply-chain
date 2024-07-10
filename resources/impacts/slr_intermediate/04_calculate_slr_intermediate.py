
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

from pipeline.direct.direct import get_sector_exposure

aqueduct_metadata_path = Path('.', 'data', 'aqueduct_download_metadata.csv')
country_bounding_box_path = Path('.', 'data', 'country_bounding_boxes.csv')
exposure_metadata_path = Path('.', 'data', 'exposure_metadata.csv')

output_dir = Path('.', 'data', 'results')
hazmap_dir = Path('.', 'data', 'intermediate')
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
# n_cpus = 1

verbose = False

country_subset = None
rp_subset = None
year_subset = None
scenario_subset = None

# country_subset = ['Cuba', 'Ireland']
rp_subset = [100]
year_subset = ['hist']
scenario_subset = ['historical', 'rcp4p5', 'rcp8p5']

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
exposure_metadata = exposure_metadata.merge(country_bounding_boxes, how='left', on=['country'])
exposure_metadata = exposure_metadata.set_index(['country', 'sector'])

# print(get_sector_exposure('refin_and_transform', 'Zimbabwe'))
# raise ValueError()


if rp_subset:
    aqueduct_metadata = aqueduct_metadata[aqueduct_metadata['rp'].isin(rp_subset)]
if year_subset:
    aqueduct_metadata = aqueduct_metadata[aqueduct_metadata['year'].isin(year_subset)]
if scenario_subset:
    aqueduct_metadata = aqueduct_metadata[aqueduct_metadata['scenario'].isin(scenario_subset)]

to_drop = []
for (country, sector), _ in exposure_metadata.iterrows():
    if country_subset and not country in country_subset:
        to_drop = to_drop + [(country, sector)]
        continue
    if sector_list and not sector in sector_list:
        to_drop = to_drop + [(country, sector)]
        continue

    future_outfiles = [
        Path(output_dir, f"{row['scenario']}_{row['subsidence']}_{row['year']}_{row['rp']}_{sector}_{country.replace(' ', '')}.csv")
        for _, row in aqueduct_metadata.iterrows()
    ]
    if np.all([os.path.exists(f) for f in future_outfiles]):
        to_drop = to_drop + [(country, sector)]
        continue

exposure_metadata.drop(to_drop, inplace=True)

def get_exposure_mappings(haz_df, transform):
    if verbose:
        print('transform')
        print(transform)
    # Partially stolen from climada.util.coordinates.match_grid_points
    x = haz_df.index.get_level_values('lon')
    y = haz_df.index.get_level_values('lat')
    xres, _, xmin, _, yres, ymin = transform[:6]
    xmin, ymin = xmin + 0.5 * xres, ymin + 0.5 * yres
    x_i = np.round((x - xmin) / xres).astype(int)
    y_i = np.round((y - ymin) / yres).astype(int)
    lons = xmin + (x_i * xres)
    lats = ymin + (y_i * yres)
    lons = np.round(lons, 5)
    lats = np.round(lats, 5)
    return pd.DataFrame(dict(
        haz_lat = y,
        haz_lon = x,
        exp_lat = lats,
        exp_lon = lons
    )).set_index(['haz_lat', 'haz_lon'])



def process_flood_df(df, exp, country, sector, crow):
    for _, row in df.iterrows():
        print(f"Working on {row['local_path']}")
        out_filename = f"{row['scenario']}_{row['subsidence']}_{row['year']}_{row['rp']}_{sector}_{country.replace(' ', '')}.csv"
        out_path = Path(output_dir, out_filename)
        if os.path.exists(out_path):
            print('Output already exists: skipping')
            continue
        filepath = row['local_path']
        slr = rxr.open_rasterio(filepath)
        subset_lons = slr.x[np.multiply(slr.x >= crow['lon_min'], slr.x <= crow['lon_max'])]
        subset_lats = slr.y[np.multiply(slr.y >= crow['lat_min'], slr.y <= crow['lat_max'])]
        subset = slr.loc[1, subset_lats, subset_lons]

        haz_df = subset.to_pandas()
        haz_df = pd.melt(haz_df, var_name = 'x', value_name='depth', ignore_index=False)
        haz_df = haz_df[haz_df['depth'] != slr._FillValue]
        haz_df = haz_df[haz_df['depth'] > 0]
        haz_df = haz_df.reset_index().rename(columns={'x': 'lon', 'y': 'lat'})
        haz_df['lat'] = np.round(haz_df['lat'], 5)  # For index matching later
        haz_df['lon'] = np.round(haz_df['lon'], 5)
        haz_df.set_index(['lat', 'lon'], inplace=True)

        # transform = crow['transform']
        # transform = eval(transform) if isinstance(transform, str) else transform
        res = np.abs(u_coord.get_resolution(exp.lat.values, exp.lon.values)).min()
        _, _, transform = u_coord.pts_to_raster_meta(
                points_bounds=(exp.lon.min(), exp.lat.min(), exp.lon.max(), exp.lat.max()),
                res = res
            )

        exp = exp[exp['value'] > 0]
        exp['lat'] = np.round(exp['lat'], 5)  # For index matching later
        exp['lon'] = np.round(exp['lon'], 5)
        mapping = get_exposure_mappings(haz_df, list(transform))

        if verbose:
            print('haz_df')
            print(haz_df.sort_index())
            print('mapping')
            print(mapping.sort_index())

        mapped = haz_df.merge(
            mapping.rename_axis(index={'haz_lat': 'lat', 'haz_lon': 'lon'}), 
            how='left', 
            left_index=True, 
            right_index=True
        )

        if verbose:
            print("STAGE ONE")
            print(mapped.sort_index())
        mapped = mapped\
            .reset_index()\
            .drop(columns=['lat', 'lon'])\
            .rename(columns={'exp_lat': 'lat', 'exp_lon': 'lon'})

        if verbose:
            print('exp_lon')
            print(list(exp.sort_values(by='lon').lon))
            print('mapped lon')
            print(list(mapped.reset_index().sort_values(by='lon')['lon']))

        mapped = mapped.merge(exp, how='inner', on=['lat', 'lon'])

        if verbose:
            print("STAGE TWO")
            print(mapped.sort_values(by=['lat', 'lon']))
            print('exp')
            print(exp.sort_values(by=['lat', 'lon']))
        if mapped.shape[0] == 0:
            print("Didn't get any matches ... suspicious")

        mapped = mapped.groupby(['lat', 'lon'])\
            .agg('max')

        if verbose:
            print("STAGE THREE")
            print(mapped.sort_values(by=['lat', 'lon']))

        mapped.to_csv(out_path)



def process_countrysector_df(df):
    for (country, sector), crow in df[::-1].iterrows():
        if country_subset and not country in country_subset:
            continue
        if sector_list and not sector in sector_list:
            continue
        print(f'Working on {country} - {sector}')

        # future_outfiles = [
        #     Path(output_dir, f"{row['scenario']}_{row['subsidence']}_{row['year']}_{row['rp']}_{sector}_{country.replace(' ', '')}.csv")
        #     for _, row in aqueduct_metadata.iterrows()
        # ]
        # if np.all([os.path.exists(f) for f in future_outfiles]):
        #     print("All outputs for this country-sector exist. Moving on.")
        #     continue

        try:
            if verbose:
                print("Getting exposure")
            exp = get_sector_exposure(sector, country).gdf
        except Exception as e:
            print("Couldn't load exposure. Skipping")
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
            continue

        if verbose:
            print("Validating exposure")
        country_iso3num = pycountry.countries.get(name=country).numeric
        if 'region_id' not in exp.columns or \
            (len(np.unique(exp.region_id)) == 1 and exp.region_id.iloc[0] == 0):
            raise ValueError("Need to assign region ids")
            # sector_exp.set_region_id()
        if len(np.unique(exp.region_id)) > 1:
            exp = exp[exp['region_id'] == int(country_iso3num)]
        if exp.shape[0] == 0:
            print(f"No region IDs for this country: {country}. Skipping")
            continue

        exp = exp.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
        exp = exp[['lat', 'lon', 'value']]
        if exp[exp['value'] > 0].shape[0] == 0:
            print("No positive exposures here. Uh oh. Skipping")
            continue

        process_flood_df(aqueduct_metadata, exp=exp, country=country, sector=sector, crow=crow)
        # chunk_size = int(np.ceil(aqueduct_metadata.shape[0] / n_cpus))
        # chunked_df = [aqueduct_metadata[::-1].iloc[ix:(ix + chunk_size)] for ix in range(0, aqueduct_metadata.shape[0], chunk_size)]
        # f_partial = partial(process_flood_df, exp=exp, country=country, sector=sector, crow=crow)

        # with pa.multiprocessing.ProcessPool(n_cpus) as pool:
        #     _ = pool.map(f_partial, chunked_df)

chunk_size = int(np.ceil(exposure_metadata.shape[0] / n_cpus))
chunked_df = [exposure_metadata.iloc[ix:(ix + chunk_size)] for ix in range(0, exposure_metadata.shape[0], chunk_size)]
# f_partial = partial(process_countrysector_df)

with pa.multiprocessing.ProcessPool(n_cpus) as pool:
    _ = pool.map(process_countrysector_df, chunked_df)