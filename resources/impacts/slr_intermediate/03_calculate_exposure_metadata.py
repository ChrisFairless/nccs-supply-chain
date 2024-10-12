import sys
sys.path.append('../../..')

import pandas as pd
import numpy as np
import os
from pathlib import Path
import itertools
from functools import reduce, partial
import traceback
import pycountry
import climada.util.coordinates as u_coord
import pathos as pa

from nccs.pipeline.direct.direct import get_sector_exposure

aqueduct_metadata_path = Path('.', 'data', 'aqueduct_download_metadata.csv')
country_bounding_box_path = Path('.', 'data', 'country_bounding_boxes.csv')
output_dir = Path('.', 'data')

country_bounding_boxes = pd.read_csv(country_bounding_box_path)

sector_list = ["agriculture", "forestry", "mining", "manufacturing", "service", "energy", "water", "waste",
                        "basic_metals", "pharmaceutical", "food", "wood", "chemical", "rubber_and_plastic",
                        "non_metallic_mineral", "refin_and_transform"]
# sector_list = ["mining", "manufacturing"]
# sector_list = ['service']

# n_cpus = pa.helpers.cpu_count() - 1

output_path = Path(output_dir, 'exposure_metadata.csv')
assert(os.path.exists(output_dir))

total_exposures = pd.DataFrame(columns=['sector', 'country', 'value', 'res', 'nrow', 'ncol', 'transform']).set_index(['sector', 'country'])


# test_transform_values = [1, 2, 3, 4, 5, 6, 7, 8]
# total_exposures.loc[('test', 'test')] = dict(
#     value = 1000.0,
#     res = 0.1,
#     nrow = 10,
#     ncol = 20,
#     transform = test_transform_values
# )

for sector in sector_list:
    print(f"Working on sector {sector}")
    for _, crow in country_bounding_boxes.iterrows():
        country = crow['country']
        country_iso3num = pycountry.countries.get(name=crow['country']).numeric
        print(f"Working on country {country}")
        try:
            sector_exp = get_sector_exposure(sector, crow['country'])
        except Exception as e:
            print("... couldn't get exposures from the API for some reason. Skipping.")
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
            # total_exposures.loc[(sector, country), 'value'] = np.nan
            continue

        try:
            if 'region_id' not in sector_exp.gdf.columns or \
            (len(np.unique(sector_exp.gdf.region_id)) == 1 and sector_exp.gdf.region_id.iloc[0] == 0):
                print("... assigning region ids")
                sector_exp.set_region_id()
            if len(np.unique(sector_exp.gdf.region_id)) > 1:
                sector_exp.gdf = sector_exp.gdf[sector_exp.gdf['region_id'] == int(country_iso3num)]
            if sector_exp.gdf.shape[0] == 0:
                print(f"No region IDs for this country: {crow['country']}. Skipping")
                # total_exposures.loc[(sector, country), 'value'] = np.nan
                continue

            res = np.abs(u_coord.get_resolution(
                    sector_exp.gdf.latitude.values,
                    sector_exp.gdf.longitude.values)
                    ).min()
            # Actually this is wrong, sorry, we added a buffer and also one sector bounds isn't the same as others. Phooey.
            nrow, ncol, transform = u_coord.pts_to_raster_meta(
                points_bounds=(crow['lon_min'], crow['lat_min'], crow['lon_max'], crow['lat_max']),
                res = res
            )
            new_entry = dict(
                value = sum(sector_exp.gdf['value']),
                res = res,
                nrow = nrow,
                ncol = ncol,
                transform = list(transform)
            )
            total_exposures.loc[(sector, country), :] = new_entry

        except Exception as e:
            print("... couldn't calculate sector totals for some reason. Skipping.")
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))
            total_exposures.loc[(sector, country), 'value'] = np.nan

# total_exposures.to_csv(output_path)
# total_exposures.drop(['test', 'test'])
total_exposures.to_csv(output_path)


