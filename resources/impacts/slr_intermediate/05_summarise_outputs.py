import sys
sys.path.append('../../..')

import pandas as pd
import numpy as np
import os
from pathlib import Path
import itertools
from functools import reduce, partial
import traceback

from nccs.pipeline.direct.direct import get_sector_exposure

aqueduct_metadata_path = Path('.', 'data', 'aqueduct_download_metadata.csv')
country_bounding_box_path = Path('.', 'data', 'country_bounding_boxes.csv')
total_value_path = Path('.', 'data', 'total_exposure_values.csv')
output_dir = Path('.', 'data', 'results')
# aqueduct_metadata_path = Path('.', 'resources', 'impacts', 'slr_intermediate', 'data', 'aqueduct_download_metadata.csv')
# country_bounding_box_path = Path('.', 'resources', 'impacts', 'slr_intermediate', 'data', 'country_bounding_boxes.csv')
# output_dir = Path('.', 'resources', 'impacts', 'slr_intermediate', 'data', 'results')

aqueduct_metadata = pd.read_csv(aqueduct_metadata_path)
country_bounding_boxes = pd.read_csv(country_bounding_box_path)
total_value_df = pd.read_csv(total_value_path).set_index(['sector', 'country'])
flood_thresholds = [0, 0.5, 1, 1.5, 2, 3, 4, 5]

sector_list = ["agriculture", "forestry", "mining", "manufacturing", "service", "energy", "water", "waste",
                        "basic_metals", "pharmaceutical", "food", "wood", "chemical", "rubber_and_plastic",
                        "non_metallic_mineral", "refin_and_transform"]
# sector_list = ["mining", "manufacturing"]
# sector_list = ['service']

verbose = True
include_missing = False

assert(os.path.exists(output_dir))

aqueduct_metadata = aqueduct_metadata[aqueduct_metadata['perc'] != 50]  # not ready for this yet


def summarise_flooding(sector, crow, row, total_assets, output_dir, include_missing):
    if not total_assets:
        if include_missing:
            return [
                dict(
                    scenario = row['scenario'],
                    subsidence = row['subsidence'],
                    year = row['year'],
                    rp = 1.5 if row['rp'] == 1 else row['rp'],
                    country = crow['country'],
                    sector = sector,
                    total_assets = np.nan,
                    flood_depth_threshold = threshold,
                    assets_affected = np.nan,
                    pct_assets_affected = np.nan
                ) for threshold in flood_thresholds
            ]
        else:
            return []

    if verbose:
        print(f"Working on {row['local_path']}")

    in_filename = f"{row['scenario']}_{row['subsidence']}_{row['year']}_{row['rp']}_{sector}_{crow['country'].replace(' ', '')}.csv"
    in_path = Path(output_dir, in_filename)

    if not os.path.exists(in_path):
        if verbose:
            print(f"... no data available for this combination. Skipping: {in_filename}")
        if include_missing:
            return [
                    dict(
                    scenario = row['scenario'],
                    subsidence = row['subsidence'],
                    year = row['year'],
                    rp = 1.5 if row['rp'] == 1 else row['rp'],
                    country = crow['country'],
                    sector = sector,
                    total_assets = total_assets,
                    flood_depth_threshold = threshold,
                    assets_affected = None,
                    pct_assets_affected = None
                ) for threshold in flood_thresholds
            ]
        else:
            return []

    exp_affected = pd.read_csv(in_path)

    out_list = []
    for threshold in flood_thresholds:
        out = dict(
            scenario = row['scenario'],
            subsidence = row['subsidence'],
            year = row['year'],
            rp = 1.5 if row['rp'] == 1 else row['rp'],
            country = crow['country'],
            sector = sector,
            total_assets = total_assets,
            flood_depth_threshold = threshold,
            assets_affected = sum(exp_affected[exp_affected['depth'] >= threshold]['value'])
        )
        out['pct_assets_affected'] = 0 if out['assets_affected'] == 0 else out['assets_affected'] / out['total_assets']
        out_list = out_list + [out]
    return out_list
    

combined_out = []
combined_out_filename = "risk_stats_ALL.csv"
combined_out_path = Path(output_dir, combined_out_filename)

for sector in sector_list:
    print(f"Working on sector {sector}")
    for _, crow in country_bounding_boxes.iterrows():
        print(f"Working on country {crow['country']}")
        # combined_out = []
        # combined_out_filename = f"risk_stats_{sector}_{crow['country']}.csv"
        # combined_out_path = Path(output_dir, combined_out_filename)
        # if os.path.exists(combined_out_path):
        #     print("... output already exists. Skipping.")
        #     continue

        total_assets = total_value_df.loc[(sector, crow['country']), 'value']

        for _, row in aqueduct_metadata.iterrows():
            combined_out = combined_out + summarise_flooding(sector, crow, row, total_assets, output_dir, include_missing)

combined_out = pd.DataFrame(combined_out)
combined_out.to_csv(combined_out_path)
