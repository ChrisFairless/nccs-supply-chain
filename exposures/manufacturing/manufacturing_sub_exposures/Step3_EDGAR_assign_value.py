import pandas as pd
import xarray
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt

import pycountry

from climada.entity import Exposures
import climada.util.coordinates as u_coord
from climada_petals.engine import SupplyChain

import logging
LOGGER = logging.getLogger()

from exposures.utils import root_dir

# Get the root directory
project_root = root_dir()

worldmap = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))

def get_manufacturing_exp(data, countries, mriot_type, mriot_year, repr_sectors, variable):

    glob_prod, repr_sectors, IO_countries = get_prod_secs(mriot_type, mriot_year, repr_sectors)

    cnt_dfs = []
    for iso3_cnt in countries:
        cnt_df = data.loc[data['region_id'] == iso3_cnt]

        # calculate total emssions per country (tons)
        country_sum_emissions = cnt_df['emission_t'].sum()

        # normalize each emission with the total emisions
        # Attempt to calculate total area and normalize if it's non-zero
        try:
            if country_sum_emissions != 0:
                # Normalize 'emissions' values by dividing by total area
                cnt_df['normalized_emissions'] = cnt_df['emission_t'] / country_sum_emissions
                print(f"Total emissions {iso3_cnt} is {country_sum_emissions}")
            else:
                cnt_df['normalized_emissions'] = cnt_df['emission_t']
                print(f"Total area of {iso3_cnt} is zero. Cannot perform normalization of emissions.")
        except Exception as e:
            print(f"Emissions of {cnt_df} is not zero")
            # Handle the error as needed

        try:
            # For countries that are explicitely in the MRIO  table:
            cnt_df['value'] = cnt_df['normalized_emissions'] * (glob_prod.loc[iso3_cnt].loc[repr_sectors].sum().values[0])
        except KeyError:
            # For Rest of the world countries:
            LOGGER.warning(
                "your are simulating a country for which there are no specific production data in the chose IO --> ROW country")

            ROW_manufac_prod = get_ROW_factor_WorldBank_manufac(mriot_year, IO_countries, countries)
            try:
                ROW_manufac_prod_factor = \
                ROW_manufac_prod.loc[ROW_manufac_prod['Country Code'] == iso3_cnt, 'Normalized_Prod'].values[0]
                ROW_country_production = (
                            (glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_manufac_prod_factor)
                cnt_df['value'] = cnt_df['normalized_emissions'] * ROW_country_production
            except:
                print(f"For the country {iso3_cnt} there is no MP value available, 0 value is assigned")
                ROW_manufac_prod_factor = 0
                ROW_country_production = (
                            (glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_manufac_prod_factor)
                cnt_df['value'] = cnt_df['normalized_emissions'] * ROW_country_production

            # # TODO Insert if statements to call different functions depending on the variable


            # if variable == 'food_and_paper': #TODO Food and paper function does work, but there are not a lot of countries in it, should I still take it?
            #     #Distribute value according to WorldBank Food production
            #     ROW_food_prod = get_ROW_factor_WorldBank_food(mriot_year, IO_countries, countries)
            #     try:
            #         ROW_food_prod_factor = ROW_food_prod.loc[ROW_food_prod['Country Code'] == iso3_cnt, 'Normalized_Prod'].values[0]
            #         ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_food_prod_factor)
            #         cnt_df['value'] = cnt_df['normalized_emissions'] * ROW_country_production
            #     except:
            #         print(f"For the country {iso3_cnt} there is no Food production value available, 0 value is assigned")
            #         ROW_food_prod_factor = 0
            #         ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_food_prod_factor)
            #         cnt_df['value'] = cnt_df['normalized_emissions'] * ROW_country_production

            # if variable == 'chemical_process': #TODO chemical does work, but there are not a lot of countries in it, should I still take it?
            #     #Distribute value according to WorldBank chemcial production
            #     ROW_chemical_prod = get_ROW_factor_WorldBank_food(mriot_year, IO_countries, countries)
            #     try:
            #         ROW_chemical_prod_factor = ROW_chemical_prod.loc[ROW_food_prod['Country Code'] == iso3_cnt, 'Normalized_Prod'].values[0]
            #         ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_chemical_prod_factor)
            #         cnt_df['value'] = cnt_df['normalized_emissions'] * ROW_country_production
            #     except:
            #         print(f"For the country {iso3_cnt} there is no Chemical Production value available, 0 value is assigned")
            #         ROW_chemical_prod_factor = 0
            #         ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_chemical_prod_factor)
            #         cnt_df['value'] = cnt_df['normalized_emissions'] * ROW_country_production


            # elif variable == 'refin_and_transform':
            #     #Distribute value according to WorldBank manufacturing production
            #     ROW_manufac_prod = get_ROW_factor_WorldBank_manufac(mriot_year, IO_countries, countries)
            #     try:
            #         ROW_manufac_prod_factor = ROW_manufac_prod.loc[ROW_manufac_prod['Country Code'] == iso3_cnt, 'Normalized_Prod'].values[0]
            #         ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_manufac_prod_factor)
            #         cnt_df['value'] = cnt_df['normalized_emissions'] * ROW_country_production
            #     except:
            #         print(f"For the country {iso3_cnt} there is no MP value available, 0 value is assigned")
            #         ROW_manufac_prod_factor = 0
            #         ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_manufac_prod_factor)
            #         cnt_df['value'] = cnt_df['normalized_emissions'] * ROW_country_production

        # Add more elif statements as needed for other variables

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

def get_ROW_factor_WorldBank_food(mriot_year, IO_countries, countries):
    IO_countries = IO_countries

    #load the Worldbank data
    WB_manufac = pd.read_csv(f"{project_root}/exposures/manufacturing/manufacturing_general_exposure/WorldBank_Manufac_output_without_regions.csv")
    Food_manufact = pd.read_csv(f"{project_root}/exposures/manufacturing/manufacturing_sub_exposures/WorldBank_food_perc_of_manufac_without_regions.csv")

    # Select only the specified year column and filter rows based on the 'Country Code',
    # select only the countries with are not within the IO table
    ROW_manufac_worldbank = WB_manufac[['Country Code', str(mriot_year)]][~WB_manufac['Country Code'].isin(IO_countries)]
    ROW_food_worldbank = Food_manufact[['Country Code', str(mriot_year)]][~Food_manufact['Country Code'].isin(IO_countries)]

    # select only the countries which are in the countries list (and not in the IO from before)
    filtered_manufac_worldbank = ROW_manufac_worldbank[ROW_manufac_worldbank['Country Code'].isin(countries)]
    filtered_food_worldbank = ROW_food_worldbank[ROW_food_worldbank['Country Code'].isin(countries)]


    #Combine the GDP with the mineral rent to get back to a production
    merged_df = pd.merge(filtered_manufac_worldbank, filtered_food_worldbank, on='Country Code',
                         suffixes=('_manufac', '_food'))

    #Divide the manufac by 100 and multiply it with the food (in % of manufac) to get back to a production in USD per country
    merged_df[f'{str(mriot_year)}_food_production'] = (merged_df['2011_manufac'] / 100) * merged_df['2011_food']
    food_production_worldbank = merged_df[['Country Code', f'{str(mriot_year)}_food_production']].copy()

    ROW_total_food_prodoction = food_production_worldbank[f'{str(mriot_year)}_food_production'].sum()
    # Create a new column with normalized GDP values
    food_production_worldbank['Normalized_production'] = food_production_worldbank[f'{str(mriot_year)}_food_production'] / ROW_total_food_prodoction
    return food_production_worldbank

def get_ROW_factor_WorldBank_chemical(mriot_year, IO_countries, countries):
    IO_countries = IO_countries

    #load the Worldbank data
    WB_manufac = pd.read_csv(f"{project_root}/exposures/manufacturing/manufacturing_general_exposure/WorldBank_Manufac_output_without_regions.csv")
    Chemical_manufact = pd.read_csv(f"{project_root}/exposures/manufacturing/manufacturing/manufacturing_sub_exposures/WorldBank_chemical_perc_of_manufac_without_regions.csv")

    # Select only the specified year column and filter rows based on the 'Country Code',
    # select only the countries with are not within the IO table
    ROW_manufac_worldbank = WB_manufac[['Country Code', str(mriot_year)]][~WB_manufac['Country Code'].isin(IO_countries)]
    ROW_chemical_worldbank = Chemical_manufact[['Country Code', str(mriot_year)]][~Chemical_manufact['Country Code'].isin(IO_countries)]

    # select only the countries which are in the countries list (and not in the IO from before)
    filtered_manufac_worldbank = ROW_manufac_worldbank[ROW_manufac_worldbank['Country Code'].isin(countries)]
    filtered_chemical_worldbank = ROW_chemical_worldbank[ROW_chemical_worldbank['Country Code'].isin(countries)]


    #Combine the GDP with the mineral rent to get back to a production
    merged_df = pd.merge(filtered_manufac_worldbank, filtered_chemical_worldbank, on='Country Code',
                         suffixes=('_manufac', '_chemcial'))

    #Divide the manufac by 100 and multiply it with the food (in % of manufac) to get back to a production in USD per country
    merged_df[f'{str(mriot_year)}_food_production'] = (merged_df['2011_manufac'] / 100) * merged_df['2011_chemcial']
    chemical_production_worldbank = merged_df[['Country Code', f'{str(mriot_year)}_chemcial_production']].copy()

    ROW_total_food_prodoction = chemical_production_worldbank[f'{str(mriot_year)}_chemcial_production'].sum()
    # Create a new column with normalized GDP values
    chemical_production_worldbank['Normalized_production'] = chemical_production_worldbank[f'{str(mriot_year)}_chemcial_production'] / ROW_total_food_prodoction
    return chemical_production_worldbank



###Using the WorldBank Manufacturing data (providing Total manufacturing sector output MRIO)
def get_ROW_factor_WorldBank_manufac(mriot_year, IO_countries, countries):
    IO_countries = IO_countries

    #load the Manufacturing of countries
    WB_manufac = pd.read_csv(f"{project_root}/exposures/manufacturing/manufacturing_general_exposure/WorldBank_Manufac_output_without_regions.csv")

    # Select only the specified year column and filter rows based on the 'Country Code',
    # select only the countries with are not within the IO table
    ROW_ManufacProd = WB_manufac[['Country Code', str(mriot_year)]][~WB_manufac['Country Code'].isin(IO_countries)]
    # select only the countries which are in the countries list (and not in the IO from before)
    filtered_ManufacProd = ROW_ManufacProd[ROW_ManufacProd['Country Code'].isin(countries)]

    ROW_total_prod = filtered_ManufacProd[str(mriot_year)].sum()
    # Create a new column with normalized GDP values
    filtered_ManufacProd['Normalized_Prod'] = filtered_ManufacProd[str(mriot_year)] / ROW_total_prod
    return filtered_ManufacProd

year = 2011
emission_threshold = 0 # Insert a threshold of NOx emissions to account for manufacturing activities only
emission_threshold_scaled = 100


# files = {
#     'food_and_paper': f'food_and_paper_NOX_emissions_{year}_above_{emission_threshold}t_0.1deg_ISO3',
#     'refin_and_transform': f'refin_and_transform_NOx_emissions_{year}_above_{emission_threshold}t_0.1deg_ISO3',
#     'chemical_process':f'chemical_process_NMVOC_emissions_{year}_above_{emission_threshold}t_0.1deg_ISO3',
#     'non_metallic_mineral': f'non_metallic_mineral_PM10_emissions_{year}_above_{emission_threshold}t_0.1deg_ISO3',
#     'basic_metals': f'basic_metals_CO_emissions_{year}_above_{emission_threshold}t_0.1deg_ISO3',
#     'pharmaceutical': f'pharmaceutical_NMVOC_emissions_{year}_above_{emission_threshold}t_0.1deg_ISO3',
#     'wood':f'wood_NOx_emissions_{year}_above_{emission_threshold_scaled}t_0.1deg_ISO3',
#     'rubber_and_plastic':f'rubber_and_plastic_NOx_emissions_{year}_above_{emission_threshold_scaled}t_0.1deg_ISO3',
#     # Add more files as needed
# }
#
# sectors = {'food_and_paper': "Manufacture of food products, beverages and tobacco products",
#            'refin_and_transform': "Manufacture of coke and refined petroleum products ",
#            'chemical_process': 'Manufacture of chemicals and chemical products ',
#            'non_metallic_mineral':'Manufacture of other non-metallic mineral products',
#            'basic_metals':'Manufacture of basic metals',
#            'pharmaceutical':'Manufacture of basic pharmaceutical products and pharmaceutical preparations',
#            'wood':'Manufacture of wood and of products of wood and cork, except furniture; manufacture of articles of straw and plaiting materials',
#            'rubber_and_plastic':'Manufacture of rubber and plastic products',
#            # Add more sectors as needed
# }

#only activate this to run for individual runs
files = {
        'wood':f'wood_NOx_emissions_{year}_above_{emission_threshold_scaled}t_0.1deg_ISO3',
}

sectors = {
        'wood':'Manufacture of wood and of products of wood and cork, except furniture; manufacture of articles of straw and plaiting materials',

}

mriot_type = 'WIOD16'
mriot_year = 2011

for variable, filename in files.items():
    data = pd.read_hdf(f"{project_root}/exposures/manufacturing/manufacturing_sub_exposures/intermediate_data_EDGAR/{filename}.h5")
    repr_sectors = sectors[variable]

    #get the countries within each sub-exposure
    countries = data["region_id"].unique().tolist()
    countries.sort()
    print(f"Total number of countries within {variable} exposure", len(countries))

    # Get the sector for the current variable
    current_sector = sectors.get(variable, "")

    # Apply the function that alters the value using MRIO
    exp = get_manufacturing_exp(data=data,
                                 countries=countries,
                                 mriot_type=mriot_type,
                                 mriot_year=mriot_year,
                                 repr_sectors=repr_sectors,
                                 variable=variable
                                 )

    # Save a shape file to check it in QGIS
    df_shape = exp.gdf.drop(columns=["emission_t", "normalized_emissions"])
    df_shape.to_file(f"{project_root}/exposures/manufacturing/manufacturing_sub_exposures/intermediate_data_EDGAR/{filename}_values_Manfac_scaled.shp", driver="ESRI Shapefile")

    # Save the final complete file to a climada available format h5
    df = exp.gdf.drop(columns=["geometry", "emission_t", "normalized_emissions"])
    df.to_hdf(f"{project_root}/exposures/manufacturing/manufacturing_sub_exposures/intermediate_data_EDGAR/{filename}_values_Manfac_scaled.h5", key="data", mode="w")

    # Count the number of zeros
    num_rows_with_zero = len(df[df['value'] == 0])
    print(f"num_rows_with_zero for {variable}", num_rows_with_zero)

    #Save individual country files
    for region_id in df['region_id'].unique():
        subset_df = df[df['region_id'] == region_id]
        filename_country = f"{project_root}/exposures/manufacturing/manufacturing_sub_exposures/intermediate_data_EDGAR/country_split/{filename}_values_Manfac_scaled_{region_id}.h5"
        subset_df.to_hdf(filename_country, key="data", mode="w")


    """Check points, not needed fot the final output, but create some credibility"""

    # #### Some checkpoints:
    #country sum of value
    value_sum_per_country = df.groupby('region_id')['value'].sum().reset_index()
    print(f"value_sum_per_country for {variable}", value_sum_per_country)
    #plot a barblot with this
    # Plot the bar chart for the sum of values per country
    # Sort the values and select the top 30
    sorted_value_sum_per_country = value_sum_per_country.sort_values(by='value', ascending=False).head(30)

    #Number of points per country
    num_points_per_country = exp.gdf.groupby('region_id').size()
    # Sort the values and select the top 30
    sorted_num_points_per_country = num_points_per_country.sort_values(ascending=False).head(30)

    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    from matplotlib.gridspec import GridSpec

    # Create a 2x2 grid of subplots
    fig = plt.figure(figsize=(30, 18))
    gs = GridSpec(2, 2, width_ratios=[2, 1])

    # Plot the world map with scatter plot
    ax0 = plt.subplot(gs[0, 0])
    worldmap.plot(color="lightgrey", ax=ax0)
    norm = Normalize(vmin=exp.gdf['value'].min(), vmax=exp.gdf['value'].mean())
    sc = ax0.scatter(exp.gdf['longitude'], exp.gdf['latitude'], c=exp.gdf['value'], cmap='cividis', norm=norm,
                     s=0.01)
    cbar = plt.colorbar(sc, ax=ax0, label='Value')
    ax0.set_xlabel('Longitude')
    ax0.set_ylabel('Latitude')
    ax0.set_title(f'{variable} Exposure with MRIO values scaled by {repr_sectors} production in M.USD')

    # Plot the bar chart for the number of points per country (switched order)
    ax2 = plt.subplot(gs[0, 1])
    sorted_num_points_per_country.plot(kind='bar', ax=ax2)
    ax2.set_ylabel('Number of Points')
    ax2.set_xlabel('Country Code')
    ax2.set_title('Top 30 Countries by Number of Points')

    # Plot the bar chart for the sum of values per country (switched order)
    ax1 = plt.subplot(gs[1, :])
    sorted_value_sum_per_country.plot(x='region_id', y='value', kind='bar', ax=ax1)
    ax1.set_ylabel('Sum of Values')
    ax1.set_xlabel('Country Code')
    ax1.set_title('Top 30 Countries by Sum of Values')

    plt.tight_layout()
    plt.savefig(f"{project_root}/exposures/manufacturing/manufacturing_sub_exposures/intermediate_data_EDGAR/{filename}_values_Manfac_scaled.png', bbox_inches='tight")
    plt.show()

    #country sum or normalized emission
    #should be 1 everwhere
    norm_emi_sum = exp.gdf.groupby('region_id')['normalized_emissions'].sum().reset_index()
    print(f"norm_emi_sum for {variable}", norm_emi_sum)

    #Check the largest production ocuntries for a given sector
    from climada_petals.engine import SupplyChain
    mriot_type = 'WIOD16'
    mriot_year = 2011
    mriot = SupplyChain.from_mriot(mriot_type=mriot_type,mriot_year=mriot_year).mriot
    sector_production = mriot.x.loc[(slice(None), repr_sectors), 'total production']
    sector_production_sorted = sector_production.sort_values(ascending=False)
    print(f"MRIO production values for sector {repr_sectors} sorted for each country", sector_production_sorted)

