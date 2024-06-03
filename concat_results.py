import glob
import pandas as pd
from utils.folder_naming import get_indirect_output_dir, get_direct_output_dir

"""
Gnerartes a csv file containg all the individual country csv files of a run

To run concat_results.py please update the RUN_TITLE
"""

### INDIRECT

RUN_TITLE = "interim_report_31_05_24"

io_approaches = ["ghosh", "leontief"]

for io_approach in io_approaches:

    data_files = glob.glob(f"{get_indirect_output_dir(RUN_TITLE)}/indirect_impacts_*{io_approach}*.csv")
    dfs = []
    for filename in data_files:
        df = pd.read_csv(filename)
        df['country_of_impact_iso_a3'] = filename.split("_")[-1].split(".")[0]
        dfs.append(df)

    DS_INDIRECT_BASE = pd.concat(dfs)
    DS_INDIRECT_BASE.rename(columns={'Unnamed: 0': 'mrio_sector_number'}, inplace=True)
    DS_INDIRECT_BASE["ref_year"] = DS_INDIRECT_BASE["ref_year"].astype(str)
    DS_INDIRECT_BASE['sector'] = [s[:50] for s in DS_INDIRECT_BASE['sector']]

    # #write a csv without a documentation (not used, since csv needs to be created with dashboard.py script)
    # DS_INDIRECT_BASE.to_csv(f"{get_indirect_output_dir(RUN_TITLE)}/{RUN_TITLE}_indirect_impacts_complete.csv")

    #Write and excel and save a documentation
    # Define terms and their definitions in dictionary format
    term_definitions = {
        'mrio_sector_number': 'sector number according to the MRIO table',
        'sector': 'sector name according to the MRIO table',
        'total_sectorial_production_mriot_CHE': 'total production of this sector in Switzerland (CHE) from MRIO table [in M USD]',
        'imaxPL': 'indirect maximum production loss (impact) to CHE sector by shocking cuntry_of_impact in sector_of_impact which depends on the number of simulation years given (at the moment 300 simulated years) [in M USD]',
        'irmaxPL': 'indirect relative maximum production loss. Percentage of the imaxPL of this sector in relation to the total production in CHE of this sector [in %]',
        'iAAPL': 'indirect average annual production loss (impact) to CHE sector by shocking cuntry_of_impact in sector_of_impact an average over the simulated year range reflecting the mean conditions [in M USD] ',
        'irAAPL': 'indirect relative average annual production loss. Percentage of the iAAPL of this sectors in relation to the total production in CHE of this sector [in %]',
        'iPL100': 'indirect production loss (impact) of events with a fixed return period of 100 to CHE sector by shocking cuntry_of_impact in sector_of_impact [in M USD]',
        'irPL100': 'indirect reative production loss at RP100. Percentage of the iPL100 impact to this sectors relation to the total production in CHE of this sector [in %]',
        'hazard_type':'hazard which impacts the country_of_impact_ with its sector_of_impact',
        'sector_of_impact': 'selected sector that was shocked by the hazard and determines the used exposure',
        'scenario': 'climate change scenario',
        'ref_year': 'year of simulation given by the hazard data',
        'country_of_impact': 'country which is directly impacted by the hazard for the sector_of_impact and propagates its signal according to the io_approach to CHE',
        'io_approach': 'propagation method of production losses through the supplychain',
        # Add other terms and definitions
    }
    # Write to Excel with multiple sheets
    output_path = f"{get_indirect_output_dir(RUN_TITLE)}/{RUN_TITLE}_indirect_impacts_complete_{io_approach}.xlsx"
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        # Write the main data to the first sheet
        DS_INDIRECT_BASE.to_excel(writer, sheet_name='Data', index=False)

        # Add README sheet with term definitions
        readme_data = {'Term': list(term_definitions.keys()), 'Definition': list(term_definitions.values())}
        readme_df = pd.DataFrame(readme_data)
        readme_df.to_excel(writer, sheet_name='README', index=False)


# # ### DIRECT
#
# RUN_TITLE = "interim_report_31_05_24"
#
#
# data_files = glob.glob(f"{get_direct_output_dir(RUN_TITLE)}/direct_impacts_*.csv")
# dfs = []
# for filename in data_files:
#     df = pd.read_csv(filename)
#     df['country_of_impact_iso_a3'] = filename.split("_")[-1].split(".")[0]
#     dfs.append(df)
#
# DS_DIRECT_BASE = pd.concat(dfs)
# DS_DIRECT_BASE.rename(columns={'Unnamed: 0': 'mrio_sector_number'}, inplace=True)
# DS_DIRECT_BASE["ref_year"] = DS_DIRECT_BASE["ref_year"].astype(str)
# DS_DIRECT_BASE['sector'] = [s[:50] for s in DS_DIRECT_BASE['sector']]
#
#
# # #write a csv without a documentation (not used, since csv needs to be created with dashboard.py script)
# # DS_DIRECT_BASE.to_csv(f"{get_direct_output_dir(RUN_TITLE)}/{RUN_TITLE}_direct_impacts_complete.csv")
#
# #Write and excel and save a documentation
# # Define terms and their definitions in dictionary format
# term_definitions = {
#     'mrio_sector_number': 'sector number according to the MRIO table',
#     'sector': 'sector name according to the MRIO table',
#     'total_sectorial_production_mriot': 'total production of this sector in country_of_impact from MRIO table [in M USD]',
#     'maxPL': 'direct maximum production loss (impact) to sector by shocking sector_of_impact which depends on the number of simulation years given (at the moment 300 years [in M USD]',
#     'rmaxPL': 'direct relative maximum production loss. Percentage of the maxPL of this sector in relation to the total production of this sector [in %]',
#     'AAPL': 'direct average annual production loss (impact) to sector by shocking sector_of_impact an average over the simulated year range reflecting the mean conditions [in M USD] ',
#     'rAAPL': 'direct relative average annual production loss. Percentage of the AAPL of this sectors in relation to the total production of this sector [in %]',
#     'PL100': 'direct production loss (impact) of events with a fixed return period of 100 to sector by shocking in sector_of_impact [in M USD]',
#     'rPL100': 'direct reative production loss at RP100. Percentage of the PL100 impact to this sectors in relation to the total production of this sector [in %]',
#     'hazard_type':'hazard which impacts the country_of_impact_ with its sector_of_impact',
#     'sector_of_impact': 'selected sector that was shocked by the hazard and determines the used exposure',
#     'scenario': 'climate change scenario',
#     'ref_year': 'year of simulation given by the hazard data',
#     'country_of_impact': 'country which is directly impacted by the hazard for the sector_of_impact',
#     # Add other terms and definitions
# }
# # Write to Excel with multiple sheets
# output_path = f"{get_direct_output_dir(RUN_TITLE)}/{RUN_TITLE}_direct_impacts_complete.xlsx"
# with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
#     # Write the main data to the first sheet
#     DS_DIRECT_BASE.to_excel(writer, sheet_name='Data', index=False)
#
#     # Add README sheet with term definitions
#     readme_data = {'Term': list(term_definitions.keys()), 'Definition': list(term_definitions.values())}
#     readme_df = pd.DataFrame(readme_data)
#     readme_df.to_excel(writer, sheet_name='README', index=False)