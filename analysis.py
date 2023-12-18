import glob
import os.path

import pandas as pd

import indirect
from calc_yearset import nccs_yearsets_simple
# from utils.s3client import download_from_s3_bucket, upload_to_s3_bucket
from direct import get_sector_exposure, nccs_direct_impacts_list_simple
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

    --> 'None' will use climate_scenario 'None' and historical will use '1980_2020' and will use "event_type": 
    "synthetic", could also use "observed"

River Flood: 
    'year_range': ['2010_2030','2030_2050','2050_2070','2070_2090','historical'], # officialy in API 'historical' 
    would be '1980_2000'
    'climate_scenario': ['rcp26', 'rcp85', 'None', 'rcp60'] # officialy in API, 'None' would be 'historical'

    --> 'None' will use climate_scenario 'historical' and ref_year = 'historical' will use '1980_2000'

Storm Europe: 
    hazard type: 'storm_europe', spatial coverage 'Europe' 
      {'res_km': ['100 km', '250 km', '500 km', '50 km'],
 'data_source': ['CMIP6', 'ERA5'],
 'climate_scenario': ['ssp585', 'ssp245', 'None', 'ssp370', 'ssp126'],
 'spatial_coverage': ['Europe'],
 'gcm': ['CMCC-CM2-SR5',  'HadGEM3-GC31-LL',  'ACCESS-ESM1-5',  'CMCC-ESM2',  'MPI-ESM1-2-HR',  'MIROC6',  'CanESM5',
  'GFDL-CM4',  'UKESM1-0-LL',  'GISS-E2-1-G',  'INM-CM5-0',  'CNRM-ESM2-1',  'CNRM-CM6-1',  'ACCESS-CM2',  'MIROC-ES2L',
  'INM-CM4-8',  'MRI-ESM2-0',  'IPSL-CM6A-LR',  'MPI-ESM1-2-LR',  'EC-Earth3-CC',  'FGOALS-g3',  'EC-Earth3',  'EC-Earth3-Veg-LR',
  'AWI-CM-1-1-MR',  'CNRM-CM6-1-HR',  'KACE-1-0-G',  'BCC-CSM2-MR',  'EC-Earth3-Veg',  'NESM3',  'HadGEM3-GC31-MM']
  
  historical (1980-2010), and a future period (2070-2100) --> but the files on the api are not called as such
    
    
Wildfire: 
    Available on API: haz_type: wildfire, 
    "climate_scenario": ['None'] # offically on API it would be "historical" 
    "year_range": ['historical']  # officialy on API it would be "2001_2020", 

    combination that are allowed:
    scenario = 'None'  & ref_year = historical
    --> 'None' will use climate_scenario 'historical' and ref_year = historical will use '2001-2020'
    --> even if another scenario is selected, it will just pick the historical one
    
Agriculture: Relative Cropyield
    hazard: 'relative_cropyield'
    sector: 'agriculture'
    scenario = 'climate_scenario': ['historical', 'rcp60'] --> at the moment we use 'None' for historical
    ref_year = 'year_range': ['1971_2001', '1980_2012', '2006_2099', '1976_2005']    --> at the moment we take 1971_2001 as historical
     'crop': ['mai', 'soy', 'whe', 'ric'] --> at the moment we use wheat
    'irrigation_status': ['firr', 'noirr'],
"""

# Check for country names with this website:
# https://github.com/flyingcircusio/pycountry/blob/main/src/pycountry/databases/iso3166-1.json
#
# country_list = ['United States']
# ALL_COUNTRIES = ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda', 'Argentina',
#                  'Armenia', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados',
#                  'Belarus', 'Belgium', 'Belize', 'Benin', 'Bhutan', 'Bolivia, Plurinational State of',
#                  'Bosnia and Herzegovina', 'Botswana', 'Brazil', 'Brunei Darussalam', 'Bulgaria', 'Burkina Faso',
#                  'Burundi', 'Cabo Verde', 'Cambodia', 'Cameroon',
#                  'Canada', 'Central African Republic', 'Chad', 'Chile', 'China', 'Colombia', 'Comoros', 'Congo',
#                  'Congo, The Democratic Republic of the', 'Costa Rica', 'Croatia', "Côte d'Ivoire",
#                  'Cuba', 'Cyprus', 'Czechia', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic',
#                  'Timor-Leste', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea',
#                  'Estonia', 'Eswatini', 'Ethiopia', 'Fiji', 'Finland', 'France', 'Gabon', 'Gambia', 'Georgia',
#                  'Germany', 'Ghana', 'Greece', 'Grenada', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana', 'Haiti',
#                  'Honduras', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran, Islamic Republic of', 'Iraq',
#                  'Ireland', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati',
#                  "Korea, Democratic People's Republic of",
#                  'Korea, Republic of', 'Kuwait', 'Kyrgyzstan', "Lao People's Democratic Republic", 'Latvia',
#                  'Lebanon',
#                  'Lesotho', 'Liberia',
#                  'Libya', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Madagascar', 'Malawi', 'Malaysia', 'Maldives',
#                  'Mali', 'Malta', 'Marshall Islands', 'Mauritania', 'Mauritius',
#                  'Mexico', 'Micronesia, Federated States of', 'Moldova, Republic of', 'Monaco', 'Mongolia',
#                  'Morocco', 'Mozambique', 'Myanmar', 'Namibia', 'Nauru', 'Nepal', 'Netherlands',
#                  'New Zealand', 'Nicaragua', 'Niger', 'Nigeria', 'North Macedonia', 'Norway', 'Oman', 'Pakistan',
#                  'Palau', 'Panama', 'Papua New Guinea', 'Paraguay', 'Peru', 'Philippines', 'Poland', 'Portugal',
#                  'Qatar', 'Romania', 'Russian Federation', 'Rwanda', 'Saint Kitts and Nevis', 'Saint Lucia',
#                  'Saint Vincent and the Grenadines', 'Samoa', 'San Marino', 'Sao Tome and Principe', 'Saudi Arabia',
#                  'Senegal', 'Seychelles', 'Sierra Leone', 'Singapore', 'Slovakia', 'Slovenia',
#                  'Solomon Islands', 'Somalia', 'South Africa', 'Spain', 'Sri Lanka', 'Sudan',
#                  'Suriname', 'Sweden', 'Switzerland', 'Syrian Arab Republic', 'Taiwan, Province of China',
#                  'Tajikistan', 'Tanzania, United Republic of', 'Thailand',
#                  'Togo', 'Tonga', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu', 'Uganda',
#                  'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'Uzbekistan',
#                  'Vanuatu', 'Venezuela, Bolivarian Republic of', 'Viet Nam', 'Yemen', 'Zambia',
#                  'Zimbabwe']
#
# hazard_list = ['relative_crop_yield']  # ['tropical_cyclone', 'river_flood', 'storm_europe', 'relative_crop_yield']
# sector_list = ['agriculture']  # 'mining', 'manufacturing', 'service', 'electricity', 'agriculture'
#
# scenario = 'historical'  # 'rcp60', 'rcp26', 'rcp45','None', 'historical'
# ref_year = '1971_2001'  # 'historical', 2040, 2060, 2080, 2020 #2020 works for river_flood only
# n_sim_years = 100
# io_approach = 'ghosh'

config = {
    "io_approach": "ghosh",
    "n_sim_years": 100,
    "runs": [
        {   
            "hazard": "tropical_cyclone",
            "sectors": ["mining", "manufacturing", "service", "electricity","agriculture"],
            "countries": ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda', 'Argentina',
                 'Armenia', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados',
                 'Belarus', 'Belgium', 'Belize', 'Benin', 'Bhutan', 'Bolivia, Plurinational State of',
                 'Bosnia and Herzegovina', 'Botswana', 'Brazil', 'Brunei Darussalam', 'Bulgaria', 'Burkina Faso',
                 'Burundi', 'Cabo Verde', 'Cambodia', 'Cameroon',
                 'Canada', 'Central African Republic', 'Chad', 'Chile', 'China', 'Colombia', 'Comoros', 'Congo',
                 'Congo, The Democratic Republic of the', 'Costa Rica', 'Croatia', "Côte d'Ivoire",
                 'Cuba', 'Cyprus', 'Czechia', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic',
                 'Timor-Leste', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea',
                 'Estonia', 'Eswatini', 'Ethiopia', 'Fiji', 'Finland', 'France', 'Gabon', 'Gambia', 'Georgia',
                 'Germany', 'Ghana', 'Greece', 'Grenada', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana', 'Haiti',
                 'Honduras', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran, Islamic Republic of', 'Iraq',
                 'Ireland', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati',
                 "Korea, Democratic People's Republic of",
                 'Korea, Republic of', 'Kuwait', 'Kyrgyzstan', "Lao People's Democratic Republic", 'Latvia',
                 'Lebanon',
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
                 'Suriname', 'Sweden', 'Syrian Arab Republic', 'Taiwan, Province of China',
                 'Tajikistan', 'Tanzania, United Republic of', 'Thailand',
                 'Togo', 'Tonga', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu', 'Uganda',
                 'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'Uzbekistan',
                 'Vanuatu', 'Venezuela, Bolivarian Republic of', 'Viet Nam', 'Yemen', 'Zambia',
                 'Zimbabwe'],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
                # {"scenario": "rcp26", "ref_year": "2040"}, #have the run for this for some countries
                # {"scenario": "rcp26", "ref_year": "2060"},
                # {"scenario": "rcp26", "ref_year": "2080"},
                # {"scenario": "rcp45", "ref_year": "2040"},
                # {"scenario": "rcp45", "ref_year": "2060"},
                # {"scenario": "rcp45", "ref_year": "2080"},
                # {"scenario": "rcp60", "ref_year": "2040"},
                {"scenario": "rcp60", "ref_year": "2060"},
                # {"scenario": "rcp60", "ref_year": "2080"},
                # {"scenario": "rcp85", "ref_year": "2040"},
                # {"scenario": "rcp85", "ref_year": "2060"}, #have the run for this for some countries
            ]
        },
        {
            "hazard": "river_flood",
            "sectors": ["mining", "manufacturing", "service", "electricity", "agriculture"],
            "countries": ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda', 'Argentina',
                 'Armenia', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados',
                 'Belarus', 'Belgium', 'Belize', 'Benin', 'Bhutan', 'Bolivia, Plurinational State of',
                 'Bosnia and Herzegovina', 'Botswana', 'Brazil', 'Brunei Darussalam', 'Bulgaria', 'Burkina Faso',
                 'Burundi', 'Cabo Verde', 'Cambodia', 'Cameroon',
                 'Canada', 'Central African Republic', 'Chad', 'Chile', 'China', 'Colombia', 'Comoros', 'Congo',
                 'Congo, The Democratic Republic of the', 'Costa Rica', 'Croatia', "Côte d'Ivoire",
                 'Cuba', 'Cyprus', 'Czechia', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic',
                 'Timor-Leste', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea',
                 'Estonia', 'Eswatini', 'Ethiopia', 'Fiji', 'Finland', 'France', 'Gabon', 'Gambia', 'Georgia',
                 'Germany', 'Ghana', 'Greece', 'Grenada', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana', 'Haiti',
                 'Honduras', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran, Islamic Republic of', 'Iraq',
                 'Ireland', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati',
                 "Korea, Democratic People's Republic of",
                 'Korea, Republic of', 'Kuwait', 'Kyrgyzstan', "Lao People's Democratic Republic", 'Latvia',
                 'Lebanon',
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
                 'Suriname', 'Sweden', 'Syrian Arab Republic', 'Taiwan, Province of China',
                 'Tajikistan', 'Tanzania, United Republic of', 'Thailand',
                 'Togo', 'Tonga', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu', 'Uganda',
                 'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'Uzbekistan',
                 'Vanuatu', 'Venezuela, Bolivarian Republic of', 'Viet Nam', 'Yemen', 'Zambia',
                 'Zimbabwe'],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
                # {"scenario": "rcp26", "ref_year": 2020},
                # {"scenario": "rcp26", "ref_year": 2040}, #have the run for this
                # {"scenario": "rcp26", "ref_year": 2060},
                # # {"scenario": "rcp26", "ref_year": 2080},
                # {"scenario": "rcp60", "ref_year": 2020},
                # {"scenario": "rcp60", "ref_year": 2040},
                {"scenario": "rcp60", "ref_year": 2060},
                # {"scenario": "rcp60", "ref_year": 2080},
                # {"scenario": "rcp85", "ref_year": 2020},
                # {"scenario": "rcp85", "ref_year": 2040},
                # {"scenario": "rcp85", "ref_year": 2060}, #have the run for this
                # {"scenario": "rcp85", "ref_year": 2080},
            ]
        },
        {
            "hazard": "wildfire",
            "sectors": ["mining", "manufacturing", "service", "electricity", "agriculture"],
            "countries": ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda', 'Argentina',
                 'Armenia', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados',
                 'Belarus', 'Belgium', 'Belize', 'Benin', 'Bhutan', 'Bolivia, Plurinational State of',
                 'Bosnia and Herzegovina', 'Botswana', 'Brazil', 'Brunei Darussalam', 'Bulgaria', 'Burkina Faso',
                 'Burundi', 'Cabo Verde', 'Cambodia', 'Cameroon',
                 'Canada', 'Central African Republic', 'Chad', 'Chile', 'China', 'Colombia', 'Comoros', 'Congo',
                 'Congo, The Democratic Republic of the', 'Costa Rica', 'Croatia', "Côte d'Ivoire",
                 'Cuba', 'Cyprus', 'Czechia', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic',
                 'Timor-Leste', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea',
                 'Estonia', 'Eswatini', 'Ethiopia', 'Fiji', 'Finland', 'France', 'Gabon', 'Gambia', 'Georgia',
                 'Germany', 'Ghana', 'Greece', 'Grenada', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana', 'Haiti',
                 'Honduras', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran, Islamic Republic of', 'Iraq',
                 'Ireland', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati',
                 "Korea, Democratic People's Republic of",
                 'Korea, Republic of', 'Kuwait', 'Kyrgyzstan', "Lao People's Democratic Republic", 'Latvia',
                 'Lebanon',
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
                 'Suriname', 'Sweden', 'Syrian Arab Republic', 'Taiwan, Province of China',
                 'Tajikistan', 'Tanzania, United Republic of', 'Thailand',
                 'Togo', 'Tonga', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu', 'Uganda',
                 'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'Uzbekistan',
                 'Vanuatu', 'Venezuela, Bolivarian Republic of', 'Viet Nam', 'Yemen', 'Zambia',
                 'Zimbabwe'],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
            ]
        },
        {
            "hazard": "storm_europe",
            "sectors": ["mining", "manufacturing", "service", "electricity", "agriculture"],
            "countries": ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda', 'Argentina',
                 'Armenia', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados',
                 'Belarus', 'Belgium', 'Belize', 'Benin', 'Bhutan', 'Bolivia, Plurinational State of',
                 'Bosnia and Herzegovina', 'Botswana', 'Brazil', 'Brunei Darussalam', 'Bulgaria', 'Burkina Faso',
                 'Burundi', 'Cabo Verde', 'Cambodia', 'Cameroon',
                 'Canada', 'Central African Republic', 'Chad', 'Chile', 'China', 'Colombia', 'Comoros', 'Congo',
                 'Congo, The Democratic Republic of the', 'Costa Rica', 'Croatia', "Côte d'Ivoire",
                 'Cuba', 'Cyprus', 'Czechia', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic',
                 'Timor-Leste', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea',
                 'Estonia', 'Eswatini', 'Ethiopia', 'Fiji', 'Finland', 'France', 'Gabon', 'Gambia', 'Georgia',
                 'Germany', 'Ghana', 'Greece', 'Grenada', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana', 'Haiti',
                 'Honduras', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran, Islamic Republic of', 'Iraq',
                 'Ireland', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati',
                 "Korea, Democratic People's Republic of",
                 'Korea, Republic of', 'Kuwait', 'Kyrgyzstan', "Lao People's Democratic Republic", 'Latvia',
                 'Lebanon',
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
                 'Suriname', 'Sweden', 'Syrian Arab Republic', 'Taiwan, Province of China',
                 'Tajikistan', 'Tanzania, United Republic of', 'Thailand',
                 'Togo', 'Tonga', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu', 'Uganda',
                 'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'Uzbekistan',
                 'Vanuatu', 'Venezuela, Bolivarian Republic of', 'Viet Nam', 'Yemen', 'Zambia',
                 'Zimbabwe'],
            "scenario_years": [
                {"scenario": "None", "ref_year": "present"},
                # {"scenario": "ssp126", "ref_year": "present"},
                # {"scenario": "ssp245", "ref_year": "present"},
                # {"scenario": "ssp370", "ref_year": "present"},
                # {"scenario": "ssp585", "ref_year": "present"},
            ]
        },

        {
            "hazard": "relative_crop_yield",
            "sectors": ["agriculture"],
            "countries": ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda', 'Argentina',
                 'Armenia', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados',
                 'Belarus', 'Belgium', 'Belize', 'Benin', 'Bhutan', 'Bolivia, Plurinational State of',
                 'Bosnia and Herzegovina', 'Botswana', 'Brazil', 'Brunei Darussalam', 'Bulgaria', 'Burkina Faso',
                 'Burundi', 'Cabo Verde', 'Cambodia', 'Cameroon',
                 'Canada', 'Central African Republic', 'Chad', 'Chile', 'China', 'Colombia', 'Comoros', 'Congo',
                 'Congo, The Democratic Republic of the', 'Costa Rica', 'Croatia', "Côte d'Ivoire",
                 'Cuba', 'Cyprus', 'Czechia', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic',
                 'Timor-Leste', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea',
                 'Estonia', 'Eswatini', 'Ethiopia', 'Fiji', 'Finland', 'France', 'Gabon', 'Gambia', 'Georgia',
                 'Germany', 'Ghana', 'Greece', 'Grenada', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana', 'Haiti',
                 'Honduras', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran, Islamic Republic of', 'Iraq',
                 'Ireland', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati',
                 "Korea, Democratic People's Republic of",
                 'Korea, Republic of', 'Kuwait', 'Kyrgyzstan', "Lao People's Democratic Republic", 'Latvia',
                 'Lebanon',
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
                 'Suriname', 'Sweden', 'Syrian Arab Republic', 'Taiwan, Province of China',
                 'Tajikistan', 'Tanzania, United Republic of', 'Thailand',
                 'Togo', 'Tonga', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu', 'Uganda',
                 'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'Uzbekistan',
                 'Vanuatu', 'Venezuela, Bolivarian Republic of', 'Viet Nam', 'Yemen', 'Zambia',
                 'Zimbabwe'],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
                {"scenario": "rcp60", "ref_year": "2006_2099"},
            ]
        }
    ]
}


def calc_supply_chain_impacts(
        country_list,
        hazard_list,
        sector_list,
        scenario,
        ref_year,
        n_sim_years,
        io_approach,
        save_by_country=False,
        save_by_hazard=False,
        save_by_sector=False,
        seed=1312
):
    ### --------------------------------- ###
    ### CALCULATE DIRECT ECONOMIC IMPACTS ###
    ### --------------------------------- ###

    # Generate a data frame with metadata, exposure objects and impact objects 
    # for each combination of input factors.
    analysis_df = nccs_direct_impacts_list_simple(hazard_list, sector_list, country_list, scenario, ref_year)

    ### ------------------- ###
    ### SAMPLE IMPACT YEARS ###
    ### ------------------- ###

    # Sample impact objects to create a yearset for each row of the data frame
    analysis_df['impact_yearset'] = nccs_yearsets_simple(
        analysis_df['impact_eventset'],
        n_sim_years, seed=seed
    )

    ### ----------------------------------- ###
    ### CALCULATE INDIRECT ECONOMIC IMPACTS ###
    ### ----------------------------------- ###

    # Generate supply chain impacts from the yearsets
    # Create a folder to output the data
    os.makedirs("results", exist_ok=True)

    # Run the Supply Chain for each country and sector and output the data needed to csv
    for _, row in analysis_df.iterrows():
        try:
            print(f"Calculating indirect impacts for {row['country']} {row['sector']}...")
            supchain = supply_chain_climada(
                get_sector_exposure(sector=row['sector'], country=row['country']),
                row['impact_yearset'],
                impacted_sector=row['sector'],
                io_approach=io_approach
            )
            dump_supchain_to_csv(
                supchain=supchain,
                haz_type=row['haz_type'],
                sector=row['sector'],
                scenario=scenario,
                ref_year=ref_year,
                country=row['country'],
                n_sim=n_sim_years,
                return_period=100,
                io_approach=io_approach
            )
        except ValueError as e:
            print(f"Error calculating indirect impacts for {row['country']} {row['sector']}: {e}")
    print("Done!\nTo show the Dashboard run:\nbokeh serve dashboard.py --show")


def run_pipeline(country_list, hazard, sector_list, scenario, ref_year, n_sim_years, io_approach):
    for country in country_list:
        try:
            calc_supply_chain_impacts(
                [country],  # replace by country_list if whole list should be calculated at once
                [hazard],
                sector_list,
                scenario,
                ref_year,
                n_sim_years,
                io_approach
            )
        except Exception as e:
            print(f"Could not calculate country {country} {sector_list} due to {e}")

    # # Postprocessing to create the final files
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


def run_pipeline_from_config(config):
    for run in config["runs"]:
        for scenario_year in run["scenario_years"]:
            run_pipeline(
                run["countries"],
                run["hazard"],
                run["sectors"],
                scenario_year["scenario"],
                scenario_year["ref_year"],
                config["n_sim_years"],
                config["io_approach"]
            )



if __name__ == "__main__":
    run_pipeline_from_config(config)
