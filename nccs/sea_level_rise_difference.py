import glob
import pandas as pd
from nccs.utils.folder_naming import get_indirect_output_dir, get_direct_output_dir

"""
Generates a difference between the baseline and the future steps of sea level rise

Uses the the raw output of the pipeline and calculates the difference of the impact between the 
baseline and the future scenario

The order is future minus past, so positive values should show and increase of the impact in the future and negative 
values should indicate less impact in the future

"""

import os
import pandas as pd

RUN_TITLE = "test_sea"

# Paths to the folder containing the CSV files and the output folder
input_folder = f"{get_indirect_output_dir(RUN_TITLE)}"
output_folder = f"{get_indirect_output_dir(RUN_TITLE)}/sea-level-difference"
columns_to_diff = ["imaxPL", "irmaxPL", "iAAPL", "irAAPL", "iPL100", "irPL100"]


# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

def parse_filename(filename):
    """
    Parse the filename into its components: sector, scenario, year, methodology, country
    Assumes filenames follow this structure:
    indirect_impacts_sea_level_rise_<hazard>_<sector>_<scenario>_<year>_<methodology>_<country>.csv
    """
    parts = filename.split('_')
    if len(parts) < 7 or not filename.startswith("indirect_impacts_sea_level_rise"):
        return None  # Skip files that don't follow the expected structure or don't match the prefix

    return {
        "prefix": "indirect_impacts",  # Keep the full prefix as part of the filename structure
        "hazard": "sea_level_rise",
        "sector": parts[5],
        "scenario": parts[6],
        "year": parts[7],
        "methodology": parts[8],
        "country": parts[9].split('.')[0],
    }

def calculate_differences(file1, file2, columns_to_diff, output_path, historical_file, future_scenario):
    """
    Calculate the differences between two CSV files and save the result.
    """
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    # Ensure both DataFrames have the same structure
    if not all(df1.columns == df2.columns):
        print(f"Skipping: Files {file1} and {file2} have mismatched columns.")
        return

    # Calculate differences
    diff_df = df1.copy()
    for col in columns_to_diff:
        if col in df1 and col in df2:
            diff_df[col] = df2[col] - df1[col]  # file2 - file1 (future minus past)

    # Modify the "scenario" and "ref_year" columns
    scenario_label = f"{historical_file['year']}_vs_{future_scenario}_2060"
    diff_df["scenario"] = scenario_label
    diff_df["ref_year"] = scenario_label

    # Save the result
    diff_df.to_csv(output_path, index=False)
    print(f"Saved difference to {output_path}")

def process_files(input_folder, columns_to_diff, output_folder):
    """
    Main function to process the files, calculate differences, and save the results.
    """
    # Read all files in the folder that start with the correct prefix
    files = [f for f in os.listdir(input_folder) if
             f.lower().endswith('.csv') and f.startswith("indirect_impacts_sea_level_rise")]

    # Group the files by methodology, sector, and country
    file_groups = {}
    for file in files:
        metadata = parse_filename(file)
        if metadata:
            key = (metadata["methodology"], metadata["sector"], metadata["country"])
            if key not in file_groups:
                file_groups[key] = []
            file_groups[key].append(metadata)

    # Process each group
    for key, group_files in file_groups.items():
        methodology, sector, country = key

        # Separate the files into historical and future scenario files
        historical_file = next((f for f in group_files if f["year"] == "historical"), None)
        future_ssp126_file = next((f for f in group_files if f["scenario"] == "ssp126" and f["year"] == "2060"), None)
        future_ssp585_file = next((f for f in group_files if f["scenario"] == "ssp585" and f["year"] == "2060"), None)

        # If there are no historical or future files, skip this group
        if not historical_file or not future_ssp126_file or not future_ssp585_file:
            continue

        # Get the path to the historical and future files
        historical_path = os.path.join(input_folder, f"{'_'.join(historical_file.values())}.csv")
        future_ssp126_path = os.path.join(input_folder, f"{'_'.join(future_ssp126_file.values())}.csv")
        future_ssp585_path = os.path.join(input_folder, f"{'_'.join(future_ssp585_file.values())}.csv")

        # Create the output filenames and paths
        output_filename_ssp126 = f"diff_{country}_{sector}_{methodology}_{historical_file['year']}_vs_ssp126_2060.csv"
        output_filename_ssp585 = f"diff_{country}_{sector}_{methodology}_{historical_file['year']}_vs_ssp585_2060.csv"
        output_path_ssp126 = os.path.join(output_folder, output_filename_ssp126)
        output_path_ssp585 = os.path.join(output_folder, output_filename_ssp585)

        # Calculate and save the differences for both scenarios
        calculate_differences(historical_path, future_ssp126_path, columns_to_diff, output_path_ssp126, historical_file, "ssp126")
        calculate_differences(historical_path, future_ssp585_path, columns_to_diff, output_path_ssp585, historical_file, "ssp585")


process_files(input_folder, columns_to_diff, output_folder)
