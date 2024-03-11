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


#Define Function that modifies the data

def get_manufacturing_exp(data,
                          countries,
                          mriot_type,
                          mriot_year,
                          repr_sectors
                   ):


    glob_prod, repr_sectors, IO_countries = get_prod_secs(mriot_type, mriot_year, repr_sectors)


    cnt_dfs = []
    for iso3_cnt in countries:
        cnt_df = data.loc[data['region_id']== iso3_cnt]

        #calculate total emssions per country (tons)
        country_sum_emissions = cnt_df['emi_nox'].sum()

        #normalize each area with the total area
        # Attempt to calculate total area and normalize if it's non-zero
        try:
            if country_sum_emissions != 0:
                # Normalize 'emissions' values by dividing by total area
                cnt_df['normalized_emissions'] = cnt_df['emi_nox'] / country_sum_emissions
                print(f"Total emissions of {iso3_cnt} NOx is {country_sum_emissions}")
            else:
                cnt_df['normalized_emissions'] = cnt_df['emi_nox']
                print(f"Total area of {iso3_cnt} is zero. Cannot perform normalization of emissions.")
        except Exception as e:
            print(f"Emissions of {cnt_df} is not zero")
            # Handle the error as needed


        try:
            # For countries that are explicitely in the MRIO  table:
            cnt_df['value'] = cnt_df['normalized_emissions'] * (glob_prod.loc[iso3_cnt].loc[repr_sectors].sum().values[0])
        except KeyError:
            #For Rest of the world countries:
            LOGGER.warning("your are simulating a country for which there are no specific production data in the chose IO --> ROW country")


            #### OPTION 3: Distribute value according to WorldBank manufacturing production
            ROW_manufac_prod = get_ROW_factor_WorldBank_manufac(mriot_year, IO_countries, countries)
            try:
                ROW_manufac_prod_factor = ROW_manufac_prod.loc[ROW_manufac_prod['Country Code'] == iso3_cnt, 'Normalized_Prod'].values[0]
                ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_manufac_prod_factor)
                cnt_df['value'] = cnt_df['normalized_emissions'] * ROW_country_production
            except:
                print(f"For the country {iso3_cnt} there is no MP value available, 0 value is assigned")
                ROW_manufac_prod_factor = 0
                ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_manufac_prod_factor)
                cnt_df['value'] = cnt_df['normalized_emissions'] * ROW_country_production






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


###Using the WorldBank Manufacturing data (providing Total manufacturing sector output MRIO)
def get_ROW_factor_WorldBank_manufac(mriot_year, IO_countries, countries):
    IO_countries = IO_countries

    #load the Manufacturing of countries
    WB_manufac = pd.read_csv(r'C:\github\nccs-correntics\manufacturing\manufacturing_general_exposure\WorldBank_Manufac_output_without_regions.csv')

    # Select only the specified year column and filter rows based on the 'Country Code',
    # select only the countries with are not within the IO table
    ROW_ManufacProd = WB_manufac[['Country Code', str(mriot_year)]][~WB_manufac['Country Code'].isin(IO_countries)]
    # select only the countries which are in the countries list (and not in the IO from before)
    filtered_ManufacProd = ROW_ManufacProd[ROW_ManufacProd['Country Code'].isin(countries)]

    ROW_total_prod = filtered_ManufacProd[str(mriot_year)].sum()
    # Create a new column with normalized GDP values
    filtered_ManufacProd['Normalized_Prod'] = filtered_ManufacProd[str(mriot_year)] / ROW_total_prod
    return filtered_ManufacProd




year=2011
mriot_type='WIOD16'
mriot_year=2011
#all the manufacturing sectors of WIOD16, to be changed if another table would be used
repr_sectors=["Manufacture of food products, beverages and tobacco products",
              "Manufacture of textiles, wearing apparel and leather products",
              "Manufacture of wood and of products of wood and cork, except furniture; manufacture of articles of straw and plaiting materials",
              "Manufacture of paper and paper products",
              "Printing and reproduction of recorded media",
              "Manufacture of coke and refined petroleum products ",
              "Manufacture of chemicals and chemical products ",
              "Manufacture of basic pharmaceutical products and pharmaceutical preparations",
              "Manufacture of rubber and plastic products",
              "Manufacture of other non-metallic mineral products",
              "Manufacture of basic metals",
              "Manufacture of fabricated metal products, except machinery and equipment",
              "Manufacture of computer, electronic and optical products",
              "Manufacture of electrical equipment",
              "Manufacture of machinery and equipment n.e.c.",
              "Manufacture of motor vehicles, trailers and semi-trailers",
              "Manufacture of other transport equipment",
              "Manufacture of furniture; other manufacturing",
]

data = pd.read_hdf(f"C:/github/nccs-correntics/manufacturing/manufacturing_general_exposure/intermediate_data_EDGAR/global_noxemissions_{year}_above_100t_0.1deg_ISO3.h5")
countries = data["region_id"].unique().tolist()
countries.sort()


#apply function that alters the value using MRIO
exp=get_manufacturing_exp(data=data,
    countries=countries,
    mriot_type=mriot_type,
    mriot_year=mriot_year,
    repr_sectors=repr_sectors
)

#TODO save the files


#Save a shape file to check it in QGIS
df_shape= exp.gdf.drop(columns=["emi_nox", "normalized_emissions"])
df_shape.to_file(f"C:/github/nccs-correntics/manufacturing/manufacturing_general_exposure/intermediate_data_EDGAR/global_noxemissions_{year}_above_100t_0.1deg_ISO3_values_Manfac_scaled.shp", driver="ESRI Shapefile")

#Save final file to a climada available format h5
df = exp.gdf.drop(columns=["geometry", "emi_nox", "normalized_emissions"])
df.to_hdf(f"C:/github/nccs-correntics/manufacturing/manufacturing_general_exposure/intermediate_data_EDGAR/global_noxemissions_{year}_above_100t_0.1deg_ISO3_values_Manfac_scaled.h5", key="data", mode="w") #hih res

#count number of zeros
num_rows_with_zero = len(df[df['value'] == 0])



"""Check points, not needed fot the final output, but create some credibility"""

#
# ##total emissions
# sum_emissions= exp.gdf['emi_nox'].sum()
# print("Total emissions within grid cells in t/year", sum_emissions)
#
#

# #### Some checkpoints:
# country sum of value
value_sum_per_country = df.groupby('region_id')['value'].sum().reset_index()
print(f"value_sum_per_country for Manufacturing", value_sum_per_country)
# plot a barblot with this
# Plot the bar chart for the sum of values per country
# Sort the values and select the top 30
sorted_value_sum_per_country = value_sum_per_country.sort_values(by='value', ascending=False).head(30)

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
ax0.set_title(f'Manufacturing Exposure with MRIO values scaled by total Manufacturing production in M.USD')

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
    f'C:/github/nccs-correntics/manufacturing/manufacturing_general_exposure/intermediate_data_EDGAR/global_noxemissions_{year}_above_100t_0.1deg_ISO3_values_Manfac_scaled.png',
    bbox_inches='tight')
plt.show()

#
# #country sum or normalized emission
# #should be 1 everwhere
# norm_emi_sum = exp.gdf.groupby('region_id')['normalized_emissions'].sum().reset_index()
# print(norm_emi_sum)


# #Check the total sum of value that gets distributed to the ROW countries
# #countries that are wthin WIOD 16
# regions= ['AUS', 'AUT', 'BEL', 'BGR', 'BRA', 'CAN', 'CHE', 'CHN', 'CYP', 'CZE',
#        'DEU', 'DNK', 'ESP', 'EST', 'FIN', 'FRA', 'GBR', 'GRC', 'HRV', 'HUN',
#        'IDN', 'IND', 'IRL', 'ITA', 'JPN', 'KOR', 'LTU', 'LUX', 'LVA', 'MEX',
#        'MLT', 'NLD', 'NOR', 'POL', 'PRT', 'ROU', 'RUS', 'SVK', 'SVN', 'SWE',
#        'TUR', 'TWN', 'USA', 'ROW']
# #take out of the final matrix the total value that is assigned to the counrties
# filtered_df = value_sum_per_country[['region_id', 'value']][~value_sum_per_country['region_id'].isin(regions)]
# #Sum all the ROW values
# filtered_df['value'].sum()
# #check in the glob_prod (glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0]
# # (run debugger to get: the total value manufactuirng: 6129005.7150726), if the outcome matches, the total ROW value was assigned


