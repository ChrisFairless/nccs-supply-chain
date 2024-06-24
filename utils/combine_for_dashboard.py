import glob
import pandas as pd

from utils.folder_naming import get_indirect_output_dir, get_run_dir

RUN_TITLE = "interim_report_18_06_24_TC_calibrated"

if __name__ == '__main__':
    data_files = glob.glob(f"{get_indirect_output_dir(RUN_TITLE)}/indirect_impacts_*.csv")
    dfs = []
    for filename in data_files:
        df = pd.read_csv(filename)
        df['country_of_impact_iso_a3'] = filename.split("_")[-1].split(".")[0]

        # TODO Hotfix to be removed, because there were no io approaches in the testing files
        if "leontief" in filename:
            df['io_approach'] = "leontief"
        else:
            df['io_approach'] = "ghosh"

        dfs.append(df)
    DS_INDIRECT_BASE = pd.concat(dfs)
    DS_INDIRECT_BASE.drop(columns=['Unnamed: 0'], inplace=True)
    DS_INDIRECT_BASE["ref_year"] = DS_INDIRECT_BASE["ref_year"].astype(str)
    DS_INDIRECT_BASE["value"] = DS_INDIRECT_BASE["iAAPL"].copy()
    # DS_INDIRECT_BASE["value"] = DS_INDIRECT_BASE["impact_aai"].copy() #TODO to be removed, old configurations,
    #  and used for best guesstimate run
    DS_INDIRECT_BASE['sector'] = [s[:50] for s in DS_INDIRECT_BASE['sector']]
    DS_INDIRECT_BASE.to_csv(f"{get_indirect_output_dir(RUN_TITLE)}/complete.csv")