import glob
import os.path
import numpy as np
import pandas as pd
from typing import List

from direct_impacts.direct import nccs_direct_impacts_list_simple, get_sector_exposure
from direct_impacts.calc_yearset import nccs_yearsets_simple
from direct_impacts.io import load_impact, get_job_filename
from calc_yearset import nccs_yearsets_simple
# from utils.s3client import download_from_s3_bucket, upload_to_s3_bucket
from indirect import dump_supchain_to_csv, supply_chain_climada

"""
Climada API data availability: https://climada.ethz.ch/data-api/admin/docs 
    --> Search Datasets, 
    --> example data_type: tropical_cyclone
    --> for properties always use doubled quotation marks "", example: "climate_scenario": "None"
    --> use the hazard name for the data_type

Tropical Cyclones: 
    Climada API properties:
    'ref_year': ['2040', '2060', '2080', 'historical'], 
    'event_type': ['synthetic', 'observed'],
    'climate_scenario': ['rcp26', 'rcp45', 'None', 'rcp60', 'rcp85']

    combination that are allowed:
    scenario = 'rcp26' & ref_year = 2040
    scenario = 'rcp26' & ref_year = 2060
    scenario = 'rcp26' & ref_year = 2080
    scenario = 'rcp45' & ref_year = 2040
    scenario = 'rcp45' & ref_year = 2060
    scenario = 'rcp45' & ref_year = 2080
    scenario = 'rcp60' & ref_year = 2040
    scenario = 'rcp60' & ref_year = 2060
    scenario = 'rcp60' & ref_year = 2080
    scenario = 'None'  & ref_year = historical
    --> 'None' will use climate_scenario 'None' and historical will use '1980_2020' and will use "event_type": 
    "synthetic", could also use "observed"

River Flood: 
    'year_range': ['2010_2030','2030_2050','2050_2070','2070_2090','historical'], # officialy in API 'historical' would be '1980_2000'
    'climate_scenario': ['rcp26', 'rcp85', 'None', 'rcp60'] # officialy in API, 'None' would be 'historical'

    combination that are allowed:
    scenario = 'rcp26' & ref_year = 2020
    scenario = 'rcp26' & ref_year = 2040
    scenario = 'rcp26' & ref_year = 2060
    scenario = 'rcp26' & ref_year = 2080
    scenario = 'rcp60' & ref_year = 2020
    scenario = 'rcp60' & ref_year = 2040
    scenario = 'rcp60' & ref_year = 2060
    scenario = 'rcp60' & ref_year = 2080
    scenario = 'rcp85' & ref_year = 2020
    scenario = 'rcp85' & ref_year = 2040
    scenario = 'rcp85' & ref_year = 2060 
    scenario = 'rcp85' & ref_year = 2080
    scenario = 'None'  & ref_year = historical
    --> 'None' will use climate_scenario 'historical' and ref_year = 'historical' will use '1980_2000'

Storm Europe: 
    hazard type: 'storm_europe', spatial coverage ? 
    
    
Wildfire: 
    Available on API: haz_type: wildfire, 
    "climate_scenario": ['None'] # offically on API it would be "historical" 
    "year_range": ['historical']  # officialy on API it would be "2001_2020", 

    combination that are allowed:
    scenario = 'None'  & ref_year = historical
    --> 'None' will use climate_scenario 'historical' and ref_year = historical will use '2001-2020'
    --> even if another scenario is selected, it will just pick the historical one
    
Agriculture: Relative Cropyield
    hazard: 'relative_crop_yield'
    sector: 'agriculture'
    scenario = 'climate_scenario': ['historical', 'rcp60'] & ref_year = 'year_range': ['1971_2001', '1980_2012', '2006_2099', '1976_2005']    
    hazard_list = ['relative_crop_yield']  # ['tropical_cyclone', 'river_flood', 'storm_europe', 'relative_crop_yield']
"""




#Check for country names with this website: https://github.com/flyingcircusio/pycountry/blob/main/src/pycountry/databases/iso3166-1.json

country_list = ['United States']
ALL_COUNTRIES = ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda', 'Argentina',
                  'Armenia', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados',
                  'Belarus', 'Belgium', 'Belize', 'Benin', 'Bhutan', 'Bolivia, Plurinational State of',
                  'Bosnia and Herzegovina', 'Botswana','Brazil', 'Brunei Darussalam', 'Bulgaria', 'Burkina Faso',
                    'Burundi', 'Cabo Verde', 'Cambodia', 'Cameroon',
                  'Canada', 'Central African Republic', 'Chad', 'Chile', 'China', 'Colombia', 'Comoros', 'Congo',
                  'Congo, The Democratic Republic of the', 'Costa Rica', 'Croatia',"Côte d'Ivoire",
                  'Cuba', 'Cyprus', 'Czechia', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic',
                  'Timor-Leste', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea',
                  'Estonia', 'Eswatini', 'Ethiopia', 'Fiji', 'Finland', 'France', 'Gabon', 'Gambia', 'Georgia',
                  'Germany', 'Ghana', 'Greece', 'Grenada', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana', 'Haiti',
                  'Honduras', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran, Islamic Republic of', 'Iraq',
                  'Ireland','Israel','Italy', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati',
                  "Korea, Democratic People's Republic of",
                  'Korea, Republic of', 'Kuwait', 'Kyrgyzstan', "Lao People's Democratic Republic", 'Latvia', 'Lebanon',
                  'Lesotho', 'Liberia',
                  'Libya', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Madagascar', 'Malawi', 'Malaysia', 'Maldives',
                  'Mali', 'Malta', 'Marshall Islands', 'Mauritania', 'Mauritius',
                  'Mexico', 'Micronesia, Federated States of', 'Moldova, Republic of', 'Monaco', 'Mongolia',
                  'Morocco', 'Mozambique', 'Myanmar', 'Namibia', 'Nauru', 'Nepal', 'Netherlands',
                  'New Zealand', 'Nicaragua', 'Niger', 'Nigeria', 'North Macedonia', 'Norway', 'Oman', 'Pakistan',
                  'Palau', 'Panama', 'Papua New Guinea', 'Paraguay', 'Peru', 'Philippines', 'Poland', 'Portugal',
                  'Qatar', 'Romania', 'Russian Federation', 'Rwanda', 'Saint Kitts and Nevis', 'Saint Lucia',
                  'Saint Vincent and the Grenadines', 'Samoa', 'San Marino', 'Sao Tome and Principe', 'Saudi Arabia',
                  'Senegal', 'Seychelles', 'Sierra Leone', 'Singapore', 'Slovakia', 'Slovenia',
                  'Solomon Islands', 'Somalia', 'South Africa', 'Spain', 'Sri Lanka', 'Sudan',
                  'Suriname', 'Sweden', 'Switzerland', 'Syrian Arab Republic', 'Taiwan, Province of China',
                  'Tajikistan','Tanzania, United Republic of', 'Thailand',
                  'Togo', 'Tonga', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu', 'Uganda',
                  'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'Uzbekistan',
                  'Vanuatu', 'Venezuela, Bolivarian Republic of', 'Viet Nam', 'Yemen', 'Zambia',
                  'Zimbabwe']

hazard_list = ['relative_crop_yield']  # ['tropical_cyclone', 'river_flood', 'storm_europe', 'relative_crop_yield']
sector_list = ['agriculture'] # 'mining', 'manufacturing', 'service', 'electricity', 'agriculture'

scenario = 'historical' # 'rcp60', 'rcp26', 'rcp45','None', 'historical'
ref_year = '1971_2001' # 'historical', 2040, 2060, 2080, 2020 #2020 works for river_flood only
n_sim_years = 100
io_approach = 'ghosh'

# Agriculture
# 2006_2099, 1976_2005
# historical, rcp60

def calc_supply_chain_impacts(
        country_list: List[str],
        hazard_list: List[str],
        sector_list: List[str],
        scenario: str,
        ref_year: int,
        n_sim_years: int,
        io_approach: str,
        job_name: str = 'test',
        save_intermediate_dir: str = None,
        save_intermediate_s3: bool = False,
        load_saved_objects: bool = True,
        overwrite: bool = True,
        return_impact_objects: bool = False,
        seed: int = 1312
):
    """
    Run an end-to-end supply chain calculation.

    For each combination of country, hazard, and sector provided in the first three parameters, generate impact objects 
    for the probabilistic event sets and calculate the indirect supply chain impacts. Impact functions are inferred 
    using the `get_sector_impf` method in the direct module. Intermediate files are saved if a path or an S3 bucket 
    name is provided to the `save_intermediate_dir` or `save_intermediate_s3` parameters.

    Parameters
    ----------
    country_list : list of str
        List of countries to analyse, either as names or three-letter ISO code. Names should be consistent with the 
        pycountry module.
    hazard_list : list of str
        List of hazards to analyse. Passed to direct.get_hazard to query the CLIMADA Data API.
    sector_list : list of str
        List of sectors to analyse. Passed to direct.get_sector_exposure.
    scenario : str
        Climate scenario to analyse. Currently one of 'historical', 'ssp126', 'ssp245', 'ssp560'.
    ref_year : int
        Year to simulate. One of '2020', '2040', '2060', '2080'.
    n_sim_years : int
        Number of simulated years of events to create in the simulated yearset.
    io_approach : str
        The IO modelling approach to use, either 'leontiev' or 'ghosh'.
    job_name  : str
        A string used to create output filenames. They follow the format <jobname>_<product>_<hazard>_<sector>_<country>
        e.g. a jobname of 'test' could create test_impact_tropicalcyclone_agriculture_USA.hdf5. Default 'test'
    save_intermediate_dir : str
        If you want to save intermediate files locally, the directory to save them in. Filenames are set using the 
        `job_name` parameter. Default None
    save_intermediate_s3 : bool
        If you want to save intermediate files to an S3 bucket. Uses credentials stored in .env. Filenames are set 
        using the `job_name` parameter. Default False
    load_saved_objects : bool
        If results have already been calculated, load these from the locations specified in the previous parameters, 
        instead of re-calculating. Default False
    overwrite : bool
        Overwrite existing files. Throws an error if False when files exist. Default False
    return_impact_objects : bool
        Return impact objects in the analysis data frame. Warning: this requires a lot of memory for larger analyses. 
        Default False
    seed : int
        Random seed
    """

    ### --------------------------------- ###
    ### CALCULATE DIRECT ECONOMIC IMPACTS ###
    ### --------------------------------- ###

    # Generate a data frame with metadata, exposure objects and impact objects 
    # for each combination of input factors, and save intermediate files.
    analysis_df = nccs_direct_impacts_list_simple(
        hazard_list=hazard_list, 
        sector_list=sector_list,
        country_list=country_list,
        scenario=scenario,
        ref_year=ref_year,
        job_name=job_name,
        save_intermediate_dir=save_intermediate_dir,
        save_intermediate_s3=save_intermediate_s3,
        load_saved_objects=load_saved_objects,
        overwrite=overwrite,
        return_impact_objects=return_impact_objects
    )

    ### ------------------- ###
    ### SAMPLE IMPACT YEARS ###
    ### ------------------- ###

    # Sample the impact objects to create a yearset for each row of the data frame. Save if required.
    analysis_df = nccs_yearsets_simple(
        analysis_df=analysis_df, 
        n_sim_years=n_sim_years,
        save_intermediate_dir=save_intermediate_dir,
        save_intermediate_s3=save_intermediate_s3,
        load_saved_objects=load_saved_objects,
        overwrite=overwrite,
        return_impact_objects=return_impact_objects,
        seed=seed
    )

    ### ----------------------------------- ###
    ### CALCULATE INDIRECT ECONOMIC IMPACTS ###
    ### ----------------------------------- ###

    # Generate supply chain impacts from the yearsets
    # Create a folder to output the data
    os.makedirs("results", exist_ok=True)

    # Run the Supply Chain for each country and sector and output the data needed to csv
    for _, row in analysis_df.iterrows():
        print(f"Calculating indirect impacts for {row['country']} {row['sector']}...")
        try:
            if row['impact_yearset']:
                impact_yearset = row['impact_yearset']
            else:
                impact_yearset = load_impact(row['file_name_yearset'], save_intermediate_dir, save_intermediate_s3)
            supchain = supply_chain_climada(
                get_sector_exposure(sector=row['sector'], country=row['country']),
                impact_yearset,
                impacted_sector=row['sector'],
                io_approach='ghosh'
            )
            file_name = get_job_filename(job_name, "indirectimpacts", row['haz_type'], row['scenario'], row['ref_year'], row['sector'], row['country'], "csv")
            dump_supchain_to_csv(
                supchain=supchain,
                haz_type=row['haz_type'],
                sector=row['sector'],
                scenario=scenario,
                ref_year=ref_year,
                country=row['country'],
                n_sim=n_sim_years,
                return_period=100,
                io_approach=io_approach,
                # save_intermediate_dir=save_intermediate_dir,  # TODO
                # file_name=file_name
            )
        except ValueError as e:
            print(f"Error calculating indirect impacts for {row['country']} {row['sector']}: {e}")
    print("Done!\nTo show the Dashboard run:\nbokeh serve dashboard.py --show")



if __name__ == "__main__":
    for country in country_list:
        try:
            calc_supply_chain_impacts(
                [country],  # replace by country_list if whole list should be calculated at once
                hazard_list,
                sector_list,
                scenario,
                ref_year,
                n_sim_years,
                io_approach,
                job_name='test_main'

        save_intermediate_dir: str = None,
        save_intermediate_s3: bool = False,
        load_saved_objects: bool = True,
        overwrite: bool = True,
        return_impact_objects: bool = False,
        seed: int = 1312
            )
        except Exception as e:
            print(f"Could not calculate country {country} {sector_list} due to {e}")


    # Postprocessing to create the final files
    supchain = indirect.get_supply_chain()
    for f in glob.glob("results/*_*.csv"):
        f_out = f.replace("results", "results_row_adjusted")
        os.makedirs(os.path.dirname(f_out), exist_ok=True)

        df = pd.read_csv(f)
        iso_a3 = f.split("/")[-1].split("_")[-1].split(".")[0]
        factor = indirect.get_country_modifier(supchain, iso_a3)
        for col in df.columns:
            if col.startswith("impact_"):
                df[col] = df[col] * factor
        # df["value"] = df["value"] * factor
        print(f"Adjusting {f} by {factor} to {f_out}")
        df.to_csv(f_out, index=False)
    print("Done!\nTo show the Dashboard run:\nbokeh serve dashboard.py --show")
