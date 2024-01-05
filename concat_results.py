import glob
import pandas as pd
from utils.folder_naming import get_indirect_output_dir, get_direct_output_dir

"""
Gnerartes a csv file containg all the individual country csv files of a run

To run concat_results.py please update the RUN_TITLE
"""

### INDIRECT

RUN_TITLE = "test_run"

data_files = glob.glob(f"{get_indirect_output_dir(RUN_TITLE)}/indirect_impacts_*.csv")
dfs = []
for filename in data_files:
    df = pd.read_csv(filename)
    df['country_of_impact_iso_a3'] = filename.split("_")[-1].split(".")[0]
    dfs.append(df)

DS_INDIRECT_BASE = pd.concat(dfs)
DS_INDIRECT_BASE.rename(columns={'Unnamed: 0': 'mrio_sector_number'}, inplace=True)
DS_INDIRECT_BASE["ref_year"] = DS_INDIRECT_BASE["ref_year"].astype(str)
DS_INDIRECT_BASE['sector'] = [s[:50] for s in DS_INDIRECT_BASE['sector']]


DS_INDIRECT_BASE.to_csv(f"{get_indirect_output_dir(RUN_TITLE)}/{RUN_TITLE}_indirect_impacts_complete.csv")


### DIRECT

RUN_TITLE = "test_run"

data_files = glob.glob(f"{get_direct_output_dir(RUN_TITLE)}/direct_impacts_*.csv")
dfs = []
for filename in data_files:
    df = pd.read_csv(filename)
    df['country_of_impact_iso_a3'] = filename.split("_")[-1].split(".")[0]
    dfs.append(df)

DS_DIRECT_BASE = pd.concat(dfs)
DS_DIRECT_BASE.rename(columns={'Unnamed: 0': 'mrio_sector_number'}, inplace=True)
DS_DIRECT_BASE["ref_year"] = DS_DIRECT_BASE["ref_year"].astype(str)
DS_DIRECT_BASE['sector'] = [s[:50] for s in DS_DIRECT_BASE['sector']]



DS_DIRECT_BASE.to_csv(f"{get_direct_output_dir(RUN_TITLE)}/{RUN_TITLE}_direct_impacts_complete.csv")