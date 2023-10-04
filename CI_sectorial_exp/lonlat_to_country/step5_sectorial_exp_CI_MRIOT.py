from CI_sectorial_exp.lonlat_to_country.lonlat_to_country import get_country_vectorized_ISO, get_country_vectorized_name
from climada.util.api_client import Client
client = Client()
from climada.entity import Exposures
import pandas as pd
import pickle
from climada_petals.engine import SupplyChain



"""
#####################
######## 1 ##########
#####################
Get the critial infrastructure raster layer (needs to be first normalized with the CI index sum of each country)
"""

def get_CI_raster():

    ## Exposure
    exp_raster = Exposures.from_raster("C:/Users/AlinaMastai/Correntics/Correntics - Documents/Data/critical-infrastructure/CISI/CISI/010_degree/global.tif")
    # As always, run the check method, such that metadata can be assigned and checked for missing mandatory parameters.
    exp_raster.check()
    print('Meta:', exp_raster.meta)

    # Let's have a look at the Exposures instance!
    print('\n' + '\x1b[1;03;30;30m'  + 'exp_raster looks like:' + '\x1b[0m')
    exp_raster.gdf.head()
    exp_raster.gdf['ISO3'] = ''



    coordinates= list(zip(exp_raster.gdf.longitude,exp_raster.gdf.latitude))

    """
    Step 1
    Get the country iso for each gridcell
    """

    countries=get_country_vectorized_ISO(coordinates) #original
    #countries= get_country_vectorized_name(coordinates)
    print(countries)
    """
    Check if the list is not empty and also consists of something else
    """
    from collections import Counter

    # Assuming you have a list called 'countries'
    # Check the unique elements and their counts
    element_counts = Counter(countries)

    # Print the unique elements and their counts
    for element, count in element_counts.items():
        print(f"{element}: {count} times")

    # Check if "None" is in the list and its count
    if "None" in element_counts:
        print(f"'None' is in the list and appears {element_counts['None']} times")
    else:
        print("'None' is not in the list")


    ### asign th countries as a new column
    exp_raster.gdf['ISO3'] = countries


    """
    Save the file as a csv for intermediate results and testing to avoid heavy computations all the time
    """
    # # Define the path to save the CSV file
    # output_csv_path = 'C:/Users/AlinaMastai/Correntics/Correntics - Documents/Data/critical-infrastructure/intermediate_results/CISI_global_ISO3.csv'
    #
    # # Save the GeoDataFrame to a CSV file
    # exp_raster.gdf.to_csv(output_csv_path, index=False)

    """
    Reopen it again in the case of closed or overloaded console
    """
    #
    # import geopandas as gpd
    #
    # # Define the path to the CSV file
    # csv_path = 'C:/Users/AlinaMastai/Correntics/Correntics - Documents/Data/critical-infrastructure/intermediate_results/CISI_global_ISO3.csv'
    #
    # # Read the CSV file as a GeoDataFrame
    # reopened_gdf = gpd.read_file(csv_path)



    """
    Sum the critical infastructure for each country and save this into an excel file
    """


    # Assuming you have your extended GeoDataFrame named 'exp_raster.gdf'

    # Group by the 'Country' column and sum the 'value' column
    country_sum = exp_raster.gdf.groupby('ISO3')['value'].sum().reset_index()

    # Create a DataFrame
    df_country_sum = pd.DataFrame(country_sum)

    # # Define the path to save the Excel file
    # output_excel_path = 'C:/Users/AlinaMastai/Correntics/Correntics - Documents/Data/critical-infrastructure/intermediate_results/country_sum.xlsx'
    #
    # # Save the DataFrame to an Excel file
    # df_country_sum.to_excel(output_excel_path, index=False)


    """
    Normalize the raster data with the country sum to get a normalized CISI value
    Attention, this makes the original exp_raster.gdf smaller  as it only takes the rows which are not None for ISO3 (?)
    """

    # Assuming you have your extended GeoDataFrame named 'exp_raster.gdf'
    # Assuming you have a DataFrame named 'df_country_sum' with summed values for each country

    # Merge the 'df_country_sum' DataFrame with 'exp_raster.gdf' based on the 'ISO3' column
    exp_raster.gdf = exp_raster.gdf.merge(df_country_sum, on='ISO3', suffixes=('', '_sum'))

    # Calculate the normalized value
    exp_raster.gdf['normalized_value'] = exp_raster.gdf['value'] / exp_raster.gdf['value_sum']


    # Print the updated GeoDataFrame with the new columns
    print(exp_raster.gdf.head())

    """
    Save this raster file into an intermediate file format to use it in a later code
    use therefore the picke thing
    """
    with open("CI_raster.pkl", "wb") as f:
        pickle.dump(exp_raster, f)


    #this would be the code to open the file again-> activate this in the file to open
    # with open("cache.pkl", "rb") as f:
    #
    #     exp_raster = pickle.load(f)

    return(exp_raster)




"""
#####################
######## 2 ##########
#####################
Get the final demand data for each sector using the MRIO tables
"""

"""
To be done:
Add an aggergation over several sectors to get a total value for Service or utilities sector
try something like this: https://pymrio.readthedocs.io/en/latest/notebooks/advanced_group_stressors.html
"""


def get_sectorial_exposure(country,sector):
    """
    First:
    loading the Multi-Regional Input-Output Table of interest.
    SupplyChain computes indirect economic impacts via Input-Output (IO) modeling. At the core of IO modeling lies an Input-Output Table. SupplyChain uses the pymrio python package to download, parse and save Multi-Regional Input Output Tables (MRIOTs). In principle, any IO table can be loaded and used, as long as the structure is consistent with those internally supported by SupplyChain, which are:

    EXIOBASE3 (1995-2011; 44 countries; 163 industries)​
    WIOD16 (2000-2014; 43 countries; 56 industries)​
    OECD21 (1995-2018; 66 countries; 45 industries)​
    These MRIOTs can be downloaded, parsed and saved automatically.

    The first step is to instantiate a SupplyChain class.
    This can be done by passing a customized MRIOT or by calling the from_mriot class method and use one of the supported MRIOTs.
    """

    supchain = SupplyChain.from_mriot(mriot_type='WIOD16', mriot_year=2011)
    supchain.mriot

    # country
    supchain.mriot.get_regions()

    # sectors
    supchain.mriot.get_sectors()

    # transaction matrix
    supchain.mriot.Z

    # final demand
    supchain.mriot.Y

    # total production
    supchain.mriot.x


    final_demand = supchain.mriot.Y

    ### Get the final demand for each sector within a country
    if sector == "service":
        # List of service sectors to aggregate
        service_sectors = [
            'Construction',
            'Wholesale and retail trade and repair of motor vehicles and motorcycles',
            'Wholesale trade, except of motor vehicles and motorcycles',
            'Retail trade, except of motor vehicles and motorcycles',
            'Land transport and transport via pipelines',
            'Water transport',
            'Air transport',
            'Warehousing and support activities for transportation',
            'Postal and courier activities',
            'Accommodation and food service activities',
            'Publishing activities',
            'Motion picture, video and television programme production, sound recording and music publishing activities; programming and broadcasting activities',
            'Telecommunications',
            'Computer programming, consultancy and related activities; information service activities',
            'Financial service activities, except insurance and pension funding',
            'Insurance, reinsurance and pension funding, except compulsory social security',
            'Activities auxiliary to financial services and insurance activities',
            'Real estate activities',
            'Legal and accounting activities; activities of head offices; management consultancy activities',
            'Architectural and engineering activities; technical testing and analysis',
            'Scientific research and development',
            'Advertising and market research',
            'Other professional, scientific and technical activities; veterinary activities',
            'Administrative and support service activities',
            'Public administration and defence; compulsory social security',
            'Education',
            'Human health and social work activities',
            'Other service activities',
            'Activities of households as employers; undifferentiated goods- and services-producing activities of households for own use',
            'Activities of extraterritorial organizations and bodies'
        ]

        # Initialize total final demand for service sector
        final_demand_for_sector = 0

        # Iterate through the service sectors and sum the final demand for each sector
        for s in service_sectors:
            final_demand_for_each_sector = final_demand.loc[(country, s), 'final demand']
            final_demand_for_sector += final_demand_for_each_sector
            ### Attention: MRIO table data are in M.EUR, which means that we need to multiply the demand value with 10^6!
        final_demand_for_sector += final_demand_for_sector * 1000000

    else:
        final_demand_for_sector = final_demand.loc[(country, sector), 'final demand']
        ### Attention: MRIO table data are in M.EUR, which means that we need to multiply the demand value with 10^6!
        final_demand_for_sector += final_demand_for_sector * 1000000



    return(final_demand_for_sector)


"""
#####################
######## 3 ##########
#####################
Create sectorial exposure by multiplying the normalized CI raster data with the MRIO sectorial exposure
"""


def create_sectorial_exposure(exp_raster,country, final_demand_for_sector):

    # Multiply the exposure data with the demand for the sector  and create a new column 'sector_exposure'
    exp_raster.gdf['sector_exposure'] = exp_raster.gdf['normalized_value'] * final_demand_for_sector

    """
    Rename the columns in order for climada to work properly
    """
    # Rename the 'value' column to 'value_old'
    exp_raster.gdf = exp_raster.gdf.rename(columns={'value': 'value_old'})

    # Rename the 'pk_normalized' column to 'value'
    exp_raster.gdf = exp_raster.gdf.rename(columns={'sector_exposure': 'value'})

    """
    Assign for to the final exposure file a numeric region_id, which is required by the supplychain module
    to be precise, it is required by the calc_shock_to_sectors function
    """


    # Mapping ISO3 to ISO3166 numeric country codes
    iso3_to_iso3166 = {
        'AFG': 4,
        'ALB': 8,
        'DZA': 12,
        'ASM': 16,
        'AND': 20,
        'AGO': 24,
        'AIA': 660,
        'ATA': 10,
        'ATG': 28,
        'ARG': 32,
        'ARM': 51,
        'ABW': 533,
        'AUS': 36,
        'AUT': 40,
        'AZE': 31,
        'BHS': 44,
        'BHR': 48,
        'BGD': 50,
        'BRB': 52,
        'BLR': 112,
        'BEL': 56,
        'BLZ': 84,
        'BEN': 204,
        'BMU': 60,
        'BTN': 64,
        'BOL': 68,
        'BES': 535,
        'BIH': 70,
        'BWA': 72,
        'BVT': 74,
        'BRA': 76,
        'IOT': 86,
        'BRN': 96,
        'BGR': 100,
        'BFA': 854,
        'BDI': 108,
        'CPV': 132,
        'KHM': 116,
        'CMR': 120,
        'CAN': 124,
        'CYM': 136,
        'CAF': 140,
        'TCD': 148,
        'CHL': 152,
        'CHN': 156,
        'CXR': 162,
        'CCK': 166,
        'COL': 170,
        'COM': 174,
        'COD': 180,
        'COG': 178,
        'COK': 184,
        'CRI': 188,
        'HRV': 191,
        'CUB': 192,
        'CUW': 531,
        'CYP': 196,
        'CZE': 203,
        'CIV': 384,
        'DNK': 208,
        'DJI': 262,
        'DMA': 212,
        'DOM': 214,
        'ECU': 218,
        'EGY': 818,
        'SLV': 222,
        'GNQ': 226,
        'ERI': 232,
        'EST': 233,
        'SWZ': 748,
        'ETH': 231,
        'FLK': 238,
        'FRO': 234,
        'FJI': 242,
        'FIN': 246,
        'FRA': 250,
        'GUF': 254,
        'PYF': 258,
        'ATF': 260,
        'GAB': 266,
        'GMB': 270,
        'GEO': 268,
        'DEU': 276,
        'GHA': 288,
        'GIB': 292,
        'GRC': 300,
        'GRL': 304,
        'GRD': 308,
        'GLP': 312,
        'GUM': 316,
        'GTM': 320,
        'GGY': 831,
        'GIN': 324,
        'GNB': 624,
        'GUY': 328,
        'HTI': 332,
        'HMD': 334,
        'VAT': 336,
        'HND': 340,
        'HKG': 344,
        'HUN': 348,
        'ISL': 352,
        'IND': 356,
        'IDN': 360,
        'IRN': 364,
        'IRQ': 368,
        'IRL': 372,
        'IMN': 833,
        'ISR': 376,
        'ITA': 380,
        'JAM': 388,
        'JPN': 392,
        'JEY': 832,
        'JOR': 400,
        'KAZ': 398,
        'KEN': 404,
        'KIR': 296,
        'PRK': 408,
        'KOR': 410,
        'KWT': 414,
        'KGZ': 417,
        'LAO': 418,
        'LVA': 428,
        'LBN': 422,
        'LSO': 426,
        'LBR': 430,
        'LBY': 434,
        'LIE': 438,
        'LTU': 440,
        'LUX': 442,
        'MAC': 446,
        'MDG': 450,
        'MWI': 454,
        'MYS': 458,
        'MDV': 462,
        'MLI': 466,
        'MLT': 470,
        'MHL': 584,
        'MTQ': 474,
        'MRT': 478,
        'MUS': 480,
        'MYT': 175,
        'MEX': 484,
        'FSM': 583,
        'MDA': 498,
        'MCO': 492,
        'MNG': 496,
        'MNE': 499,
        'MSR': 500,
        'MAR': 504,
        'MOZ': 508,
        'MMR': 104,
        'NAM': 516,
        'NRU': 520,
        'NPL': 524,
        'NLD': 528,
        'NCL': 540,
        'NZL': 554,
        'NIC': 558,
        'NER': 562,
        'NGA': 566,
        'NIU': 570,
        'NFK': 574,
        'MNP': 580,
        'NOR': 578,
        'OMN': 512,
        'PAK': 586,
        'PLW': 585,
        'PSE': 275,
        'PAN': 591,
        'PNG': 598,
        'PRY': 600,
        'PER': 604,
        'PHL': 608,
        'PCN': 612,
        'POL': 616,
        'PRT': 620,
        'PRI': 630,
        'QAT': 634,
        'MKD': 807,
        'ROU': 642,
        'RUS': 643,
        'RWA': 646,
        'REU': 638,
        'BLM': 652,
        'SHN': 654,
        'KNA': 659,
        'LCA': 662,
        'MAF': 663,
        'SPM': 666,
        'VCT': 670,
        'WSM': 882,
        'SMR': 674,
        'STP': 678,
        'SAU': 682,
        'SEN': 686,
        'SRB': 688,
        'SYC': 690,
        'SLE': 694,
        'SGP': 702,
        'SXM': 534,
        'SVK': 703,
        'SVN': 705,
        'SLB': 90,
        'SOM': 706,
        'ZAF': 710,
        'SGS': 239,
        'SSD': 728,
        'ESP': 724,
        'LKA': 144,
        'SDN': 729,
        'SUR': 740,
        'SJM': 744,
        'SWE': 752,
        'CHE': 756,
        'SYR': 760,
        'TWN': 158,
        'TJK': 762,
        'TZA': 834,
        'THA': 764,
        'TLS': 626,
        'TGO': 768,
        'TKL': 772,
        'TON': 776,
        'TTO': 780,
        'TUN': 788,
        'TUR': 792,
        'TKM': 795,
        'TCA': 796,
        'TUV': 798,
        'UGA': 800,
        'UKR': 804,
        'ARE': 784,
        'GBR': 826,
        'UMI': 581,
        'USA': 840,
        'URY': 858,
        'UZB': 860,
        'VUT': 548,
        'VEN': 862,
        'VNM': 704,
        'VGB': 92,
        'VIR': 850,
        'WLF': 876,
        'ESH': 732,
        'YEM': 887,
        'ZMB': 894,
        'ZWE': 716,
        'ALA': 248
    }

    # Check if the desired ISO3 code is in the mapping
    if country in iso3_to_iso3166:
        region_id = iso3_to_iso3166[country]

        # Add the 'region_id' column to the DataFrame
        exp_raster.gdf['region_id'] = region_id
    else:
        print(f"No mapping found for ISO3 code '{country}'")

    # Print the updated DataFrame to verify the changes
    print(exp_raster)


    return(exp_raster)


"""
#####################
######## 4 ##########
#####################
Finalize the exposure creation by combining the different functions
"""

def sectorial_exp_CI_MRIOT(country, sector):

    exp_raster = get_CI_raster()

    """
    Get the final demand for each
    """

    final_demand_for_sector = get_sectorial_exposure(country,sector)

    """
    Create the sectorial exposure
    """
    ### Create expsure based on function

    sectorial_exposure_CI_MRIOT = create_sectorial_exposure(exp_raster,country,final_demand_for_sector)

    return(sectorial_exposure_CI_MRIOT)


