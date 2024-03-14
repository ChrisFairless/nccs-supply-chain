
import pandas as pd
import numpy as np

from climada.entity import Exposures
from climada_petals.engine import SupplyChain

import logging

LOGGER = logging.getLogger()

from exposures.utils import root_dir
from utils.s3client import upload_to_s3_bucket

# Get the root directory
project_root = root_dir()

def get_utilities_exp(
        countries=None,
        mriot_type='WIOD16',
        mriot_year=2011, # 2011 year used for WIOD16, update as needed
        repr_sectors=None,
        data=None):

    glob_prod, repr_sectors, IO_countries = get_prod_secs(mriot_type, mriot_year, repr_sectors)

    ## option 1: distribute ROW production value equally (not implemented)
    # n_total = 195
    # ROW_factor = (1 / (n_total - (len(set(r[0] for r in glob_prod.axes[0])) - 1)))
    # Row_country_production = ((glob_prod.loc["ROW"].loc[repr_sectors].sum()).values[0] * ROW_factor)

    ## option 2: distribute ROW production value according to GDP (implemented)
    ROW_gdp_lookup = get_ROW_factor_GDP(mriot_year, IO_countries, countries)

    cnt_dfs = []

    for iso3_cnt in countries:

        cnt_df = data.loc[data['region_id'] == iso3_cnt]

        try:
            cnt_df['value'] = glob_prod.loc[iso3_cnt].loc[repr_sectors].sum().values[0] * cnt_df["country_normalized"]
        except KeyError:
            LOGGER.warning('You are simulating a country for which there are no production data in the chosen IOT')
            # code under option 1:
            #cnt_df["value"] = Row_country_production * cnt_df["country_normalized"] # potential update to be scaled with GDP

            # code under option 2:
            try:
                ROW_gdp_factor = ROW_gdp_lookup.loc[ROW_gdp_lookup['Country Code'] == iso3_cnt, 'Normalized_GDP'].values[0]
                ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_gdp_factor)
                cnt_df['value'] = ROW_country_production * cnt_df["country_normalized"]
            except:
                print(f"For the country {iso3_cnt} there is no GDP value available, 0 value is assigned")
                ROW_gdp_factor = 0
                ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_gdp_factor)
                cnt_df['value'] = ROW_country_production * cnt_df["country_normalized"]

        cnt_dfs.append(cnt_df)

    exp = Exposures(pd.concat(cnt_dfs).reset_index(drop=True))
    exp.set_geometry_points()

    return exp

def get_prod_secs(mriot_type, mriot_year, repr_sectors):
    mriot = SupplyChain.from_mriot(mriot_type=mriot_type,
                                   mriot_year=mriot_year).mriot

    if isinstance(repr_sectors, (range, np.ndarray)):
        repr_sectors = mriot.get_sectors()[repr_sectors].tolist()

    elif isinstance(repr_sectors, str):
        repr_sectors = [repr_sectors]

    return mriot.x, repr_sectors, mriot.get_regions()

subscores = ["Subscore_energy", "Subscore_water", "Subscore_waste"]


def get_ROW_factor_GDP(mriot_year, IO_countries, countries):
    IO_countries = IO_countries

    #load the GDP of counries
    gdp_worldbank = pd.read_csv(f"{project_root}/exposures/utilities/refinement_1/GDP_Worldbank_modified_without_regions.csv")

    # Select only the specified year column and filter rows based on the 'Country Code'
    ROW_gdp_worldbank = gdp_worldbank[['Country Code', str(mriot_year)]][~gdp_worldbank['Country Code'].isin(IO_countries)]
    # Assuming ROW_gdp_worldbank is your DataFrame and country is your list of countries
    filtered_gdp_worldbank = ROW_gdp_worldbank[ROW_gdp_worldbank['Country Code'].isin(countries)]

    ROW_total_GDP = filtered_gdp_worldbank[str(mriot_year)].sum()
    # Create a new column with normalized GDP values
    ROW_gdp_worldbank['Normalized_GDP'] = ROW_gdp_worldbank[str(mriot_year)] / ROW_total_GDP

    return ROW_gdp_worldbank

for subscore in subscores:

    if subscore == "Subscore_energy":
        repr_sectors = "Electricity, gas, steam and air conditioning supply"

    elif subscore == "Subscore_water":
        repr_sectors = "Water collection, treatment and supply"

    elif subscore == "Subscore_waste":
        repr_sectors = 'Sewerage; waste collection, treatment and disposal activities; materials recovery; remediation activities and other waste management services '

    data = pd.read_hdf(f"{project_root}/exposures/utilities/refinement_1/intermediate_data/{subscore}_ISO3_normalized.h5") # file from step 4 excluding national parks and protected areas
    countries = data["region_id"].unique().tolist()
    countries.sort()

    # apply function that alters the value using MRIO
    exp = get_utilities_exp(
        countries=countries,
        mriot_type='WIOD16',
        mriot_year=2011,
        repr_sectors=repr_sectors,
    data=data)

    # Save final file to a climada available format h5
    df = exp.gdf.drop(columns='geometry')
    filename_h5 =f"{project_root}/exposures/utilities/refinement_1/{subscore}/{subscore}_MRIO.h5"
    s3_filename_h5 =f"exposures/utilities/refinement_1/{subscore}/{subscore}_MRIO.h5"
    df.to_hdf(filename_h5, key="data", mode='w') # final file to be used in CLIMADA NCCS project
    # upload the file to the s3 Bucket
    upload_to_s3_bucket(filename_h5, s3_filename_h5)
    print(f"upload of {s3_filename_h5} to s3 bucket successful")

    #Split exposure into countries
    # Save individual country files
    for region_id in df['region_id'].unique():
        subset_df = df[df['region_id'] == region_id]
        filename_country = f"{project_root}/exposures/utilities/refinement_1/{subscore}/country_split/{subscore}_MRIO_{region_id}.h5"
        s3_filename_country = f"exposures/utilities/refinement_1/{subscore}/country_split/{subscore}_MRIO_{region_id}.h5"
        subset_df.to_hdf(filename_country, key="data", mode="w")
        # upload the individual country files to s3 bucket
        upload_to_s3_bucket(filename_country, s3_filename_country)
        print(f"upload of {s3_filename_country} to s3 bucket successful")
