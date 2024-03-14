import os.path

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
worldmap = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))

from exposures.utils import root_dir
from utils.s3client import upload_to_s3_bucket

# Get the root directory
project_root = root_dir()
print(os.path.abspath(project_root))

"""
Important Note, when running the script with a new version or modifications, make sure to delete teh files on the s3 bucket
or that they are properly replace. Goal to onyl have the relevant files on the s3 bucket and no duplicates
"""

def get_mining_exp(countries=None,
                   mriot_type='WIOD16',
                   mriot_year=2011,
                   repr_sectors='Mining and quarrying'
                   ):
    glob_prod, repr_sectors, IO_countries = get_prod_secs(mriot_type, mriot_year, repr_sectors)

    data = pd.read_hdf(
        f"{project_root}/exposures/mining/refinement_1/intermediate_data_MAUS/global_miningarea_v2_30arcsecond_converted_ISO3_improved.h5")
    cnt_dfs = []
    for iso3_cnt in countries:
        cnt_df = data.loc[data['region_id'] == iso3_cnt]

        # calculate total area of mines per country
        country_sum_area = cnt_df['area'].sum()

        # normalize each area with the total area
        # Attempt to calculate total area and normalize if it's non-zero
        try:
            if country_sum_area != 0:
                # Normalize 'area' values by dividing by total area
                cnt_df['normalized_area'] = cnt_df['area'] / country_sum_area
                print(f"Total area of {iso3_cnt} mining is {country_sum_area}")
            else:
                cnt_df['normalized_area'] = cnt_df['area']
                print(f"Total area of {iso3_cnt} is zero. Cannot perform normalization of area.")
        except Exception as e:
            print(f"Area of {cnt_df} is not zero")
            # Handle the error as needed

        try:
            # For countries that are explicitely in the MRIO  table:
            cnt_df['value'] = cnt_df['normalized_area'] * (glob_prod.loc[iso3_cnt].loc[repr_sectors].sum().values[0])
        except KeyError:
            # For Rest of the world countries:
            LOGGER.warning(
                "your are simulating a country for which there are no specific production data in the chose IO --> ROW country")

            # #### OPTION 1: Distribute ROW production value equally --> Not suggested
            # #Get a percentage of the total ROW production for each ROW country
            # n_total = 195
            # #get the factor to scale each production
            # ROW_factor = (1 / (n_total - (len(set(r[0] for r in glob_prod.axes[0])) - 1)))
            # ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_factor)
            # cnt_df['value'] = cnt_df['normalized_area'] * ROW_country_production

            # #### OPTION 2: Distribute value according to GDP
            # ROW_gdp_lookup = get_ROW_factor_GDP(mriot_year, IO_countries, countries)
            # try:
            #     ROW_gdp_factor = ROW_gdp_lookup.loc[ROW_gdp_lookup['Country Code'] == iso3_cnt, 'Normalized_GDP'].values[0]
            #     ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_gdp_factor)
            #     cnt_df['value'] = cnt_df['normalized_area'] * ROW_country_production
            # except:
            #     print(f"For the country {iso3_cnt} there is no GDP value available, 0 value is assigned")
            #     ROW_gdp_factor = 0
            #     ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_gdp_factor)
            #     cnt_df['value'] = cnt_df['normalized_area'] * ROW_country_production

            #### OPTION 3: Distribute value according to WorldMiningData
            ROW_mineral_prod = get_ROW_factor_WorldMiningData(mriot_year, IO_countries, countries)
            try:
                ROW_mineral_prod_factor = \
                    ROW_mineral_prod.loc[ROW_mineral_prod['ISO3'] == iso3_cnt, 'Normalized_Prod'].values[0]
                ROW_country_production = (
                        (glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_mineral_prod_factor)
                cnt_df['value'] = cnt_df['normalized_area'] * ROW_country_production
            except:
                print(f"For the country {iso3_cnt} there is no MP value available, 0 value is assigned")
                ROW_mineral_prod_factor = 0
                ROW_country_production = (
                        (glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_mineral_prod_factor)
                cnt_df['value'] = cnt_df['normalized_area'] * ROW_country_production

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


####### Different Option to scale the ROW mining production value of the MRIO table

## Using just the GDP of the ROW countries to scale it
def get_ROW_factor_GDP(mriot_year, IO_countries, countries):
    IO_countries = IO_countries

    # load the GDP of counries
    gdp_worldbank = pd.read_csv(f"{project_root}/exposures/mining/refinement_1/core/GDP_Worldbank_modified_without_regions.csv")

    # Select only the specified year column and filter rows based on the 'Country Code',
    # select only the countries with are not within the IO table
    ROW_gdp_worldbank = gdp_worldbank[['Country Code', str(mriot_year)]][
        ~gdp_worldbank['Country Code'].isin(IO_countries)]
    # select only the countries which are in the countries list (and not in the IO from before)
    filtered_gdp_worldbank = ROW_gdp_worldbank[ROW_gdp_worldbank['Country Code'].isin(countries)]

    ROW_total_GDP = filtered_gdp_worldbank[str(mriot_year)].sum()
    # Create a new column with normalized GDP values
    filtered_gdp_worldbank['Normalized_GDP'] = filtered_gdp_worldbank[str(mriot_year)] / ROW_total_GDP
    return filtered_gdp_worldbank


### Using the Mineral Rent (provided by the WorldBank) and multiplied back with the GPD to get to a production
def get_ROW_factor_mineral_rent_GDP(mriot_year, IO_countries, countries):
    IO_countries = IO_countries

    # load the GDP of counries
    gdp_worldbank = pd.read_csv(f"{project_root}/exposures/mining/refinement_1/core/GDP_Worldbank_modified_without_regions.csv")
    mineral_rent = pd.read_csv(f"{project_root}/exposures/mining/refinement_1/core/WorldBank_mineral_rents_modified_without_regions.csv")

    # Select only the specified year column and filter rows based on the 'Country Code',
    # select only the countries with are not within the IO table
    ROW_gdp_worldbank = gdp_worldbank[['Country Code', str(mriot_year)]][
        ~gdp_worldbank['Country Code'].isin(IO_countries)]
    ROW_mineral_rent_worldbank = mineral_rent[['Country Code', str(mriot_year)]][
        ~mineral_rent['Country Code'].isin(IO_countries)]

    # select only the countries which are in the countries list (and not in the IO from before)
    filtered_gdp_worldbank = ROW_gdp_worldbank[ROW_gdp_worldbank['Country Code'].isin(countries)]
    filtered_mineral_rent_worldbank = ROW_mineral_rent_worldbank[
        ROW_mineral_rent_worldbank['Country Code'].isin(countries)]

    # Combine the GDP with the mineral rent to get back to a production
    merged_df = pd.merge(filtered_gdp_worldbank, filtered_mineral_rent_worldbank, on='Country Code',
                         suffixes=('_gdp', '_mineral_rent'))

    # Divide the GDP by 100 and multiply it with the mineral rent (in % of GDP) to get back to a production in USD per country
    merged_df[f'{str(mriot_year)}_mineral_production'] = (merged_df['2011_gdp'] / 100) * merged_df['2011_mineral_rent']
    mineral_production_worldbank = merged_df[['Country Code', f'{str(mriot_year)}_mineral_production']].copy()

    ROW_total_mineral_prodoction = mineral_production_worldbank[f'{str(mriot_year)}_mineral_production'].sum()
    # Create a new column with normalized GDP values
    mineral_production_worldbank['Normalized_production'] = mineral_production_worldbank[
                                                                f'{str(mriot_year)}_mineral_production'] / ROW_total_mineral_prodoction
    return mineral_production_worldbank


###Using the World Mining Data (providing Total mineral production with adequate products such as in MRIO)
def get_ROW_factor_WorldMiningData(mriot_year, IO_countries, countries):
    IO_countries = IO_countries

    # load the MP (mineral production) of countries
    WorldMiningData = pd.read_excel(f"{project_root}/exposures/mining/refinement_1/core/WorldMiningData_2021_Total_Mineral_Production.xlsx")

    # Select only the specified year column and filter rows based on the 'Country Code',
    # select only the countries with are not within the IO table
    ROW_MiningProd = WorldMiningData[['ISO3', 'Total Value Mineral Production (incl. Bauxite)']][
        ~WorldMiningData['ISO3'].isin(IO_countries)]
    # select only the countries which are in the countries list (and not in the IO from before)
    filtered_MiningProd = ROW_MiningProd[ROW_MiningProd['ISO3'].isin(countries)]

    ROW_total_prod = filtered_MiningProd['Total Value Mineral Production (incl. Bauxite)'].sum()
    # Create a new column with normalized GDP values
    filtered_MiningProd['Normalized_Prod'] = filtered_MiningProd[
                                                 'Total Value Mineral Production (incl. Bauxite)'] / ROW_total_prod
    return filtered_MiningProd


data = pd.read_hdf(
    f"{project_root}/exposures/mining/refinement_1/intermediate_data_MAUS/global_miningarea_v2_30arcsecond_converted_ISO3_improved.h5")
countries = data["region_id"].unique().tolist()
countries.sort()

# apply function that alters the value using MRIO
exp = get_mining_exp(
    countries=countries,
    mriot_type='WIOD16',
    mriot_year=2011,
    repr_sectors='Mining and quarrying'
)

"""
Saving of file, first, locally and secondly also to the s3 Bukcet
"""

# Save a shape file to check it in QGIS
df_shape = exp.gdf.drop(columns=["area", "normalized_area"])
filename_shp = f"{project_root}/exposures/mining/refinement_1/global_miningarea_v2_30arcsecond_converted_ISO3_improved_values_MP_scaled.shp"
s3_filename_shp =f"exposures/mining/refinement_1/global_miningarea_v2_30arcsecond_converted_ISO3_improved_values_MP_scaled.shp"
df_shape.to_file(filename_shp,driver="ESRI Shapefile")
# upload the file to the s3 Bucket
upload_to_s3_bucket(filename_shp, s3_filename_shp)
print(f"upload of {s3_filename_shp} to s3 bucket successful")


# Save final file to a climada available format h5
df = exp.gdf.drop(columns=["geometry", "area", "normalized_area"])
filename_h5 = f"{project_root}/exposures/mining/refinement_1/global_miningarea_v2_30arcsecond_converted_ISO3_improved_values_MP_scaled.h5"
s3_filename_h5 =f"exposures/mining/refinement_1/global_miningarea_v2_30arcsecond_converted_ISO3_improved_values_MP_scaled.h5"
df.to_hdf(filename_h5,key="data", mode="w")  # hih res
# upload the file to the s3 Bucket
upload_to_s3_bucket(filename_h5, s3_filename_h5)
print(f"upload of {s3_filename_h5} to s3 bucket successful")

# Save individual country files
for region_id in df['region_id'].unique():
    subset_df = df[df['region_id'] == region_id]
    filename_country = f"{project_root}/exposures/mining/refinement_1/country_split/global_miningarea_v2_30arcsecond_converted_ISO3_improved_values_MP_scaled_{region_id}.h5"
    s3_filename_country =f"exposures/mining/refinement_1/country_split/global_miningarea_v2_30arcsecond_converted_ISO3_improved_values_MP_scaled_{region_id}.h5"
    subset_df.to_hdf(filename_country, key="data", mode="w")
    #upload the individual country files to s3 bucket
    upload_to_s3_bucket(filename_country, s3_filename_country)
    print(f"upload of {s3_filename_country} to s3 bucket successful")






# count number of zeros
num_rows_with_zero = len(df[df['value'] == 0])

# #### Some checkpoints:

# plot the exposre map
from matplotlib.colors import Normalize

fig, ax = plt.subplots(figsize=(30, 12))
worldmap.plot(color="lightgrey", ax=ax)
# Use scatter to plot the points with color based on the 'value' column
norm = Normalize(vmin=exp.gdf['value'].min(), vmax=exp.gdf['value'].mean())
sc = ax.scatter(exp.gdf['longitude'], exp.gdf['latitude'], c=exp.gdf['value'], cmap='viridis', norm=norm, s=0.01)
# Add a colorbar
cbar = plt.colorbar(sc, ax=ax, label='Value')
# Set axis labels and title
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title('Mining Exposure with MRIO values scaled by area of the mine in M.USD')
# Show the plot
plt.show()

# country sum of value
value_sum_per_country = df.groupby('region_id')['value'].sum().reset_index()
print(f"value_sum_per_country for Mining", value_sum_per_country)
# plot a barblot with this
# Plot the bar chart for the sum of values per country
# Sort the values and select the top 30
sorted_value_sum_per_country = value_sum_per_country.sort_values(by='value', ascending=False).head(30)
print(f"sorted_value_sum_per_country for Mining", sorted_value_sum_per_country)

# Number of points per country
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
ax0.set_title(f'Mining Exposure with MRIO values scaled by area of the mine in M.USD')

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
plt.savefig(
    f"{project_root}/exposures/mining/refinement_1/intermediate_data_MAUS/global_miningarea_v2_30arcsecond_converted_ISO3_improved_values_MP_scaled.png",
    bbox_inches='tight')
plt.show()

##total area
sum_area = exp.gdf['area'].sum()
print("Total area within grid cells in sqkm", sum_area)
print("area covered in  apper is 101'583km2")

# country sum of value
value_sum_per_country = df.groupby('region_id')['value'].sum().reset_index()
print(value_sum_per_country)

# country sum or normalized area
# should be 1 everwhere
norm_area_sum = exp.gdf.groupby('region_id')['normalized_area'].sum().reset_index()
print(norm_area_sum)

# Check the total sum of value that gets distributed to the ROW countries
# countries that are wthin WIOD 16
regions = ['AUS', 'AUT', 'BEL', 'BGR', 'BRA', 'CAN', 'CHE', 'CHN', 'CYP', 'CZE',
           'DEU', 'DNK', 'ESP', 'EST', 'FIN', 'FRA', 'GBR', 'GRC', 'HRV', 'HUN',
           'IDN', 'IND', 'IRL', 'ITA', 'JPN', 'KOR', 'LTU', 'LUX', 'LVA', 'MEX',
           'MLT', 'NLD', 'NOR', 'POL', 'PRT', 'ROU', 'RUS', 'SVK', 'SVN', 'SWE',
           'TUR', 'TWN', 'USA', 'ROW']
# take out of the final matrix the total value that is assigned to the counrties
filtered_df = value_sum_per_country[['region_id', 'value']][~value_sum_per_country['region_id'].isin(regions)]
# Sum all the ROW values
filtered_df['value'].sum()
# check in the glo_prod (run debugger to get: the total value of ROW mining: 2593254), if the outcome matches, the total ROW value was assigned
