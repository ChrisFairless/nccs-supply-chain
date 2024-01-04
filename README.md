

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
  'INM-CM4-8',  'MRI-ESM2-0',  'IPSL-CM6A-LR',  'MPI-ESM1-2-LR',  'EC-Earth3-CC',  'FGOALS-g3',  'EC-Earth3',  
  'EC-Earth3-Veg-LR',
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
    ref_year = 'year_range': ['1971_2001', '1980_2012', '2006_2099', '1976_2005']    --> at the moment we take 
    1971_2001 as historical
     'crop': ['mai', 'soy', 'whe', 'ric'] --> at the moment we use wheat
    'irrigation_status': ['firr', 'noirr'],
    
https://github.com/flyingcircusio/pycountry/blob/main/src/pycountry/databases/iso3166-1.json