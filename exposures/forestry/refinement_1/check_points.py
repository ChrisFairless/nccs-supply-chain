import pandas as pd
import geopandas as gpd


df = pd.read_hdf('data/forestry_values_MRIO_avg(WB-v2).h5')
colum_latitude = 'latitude'
column_longitude = 'longitude'
df[colum_latitude] = pd.to_numeric(df[colum_latitude], errors='coerce')
df[column_longitude] = pd.to_numeric(df[column_longitude], errors='coerce')
# Create a GeoDataFrame from the latitude and longitude columns
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[column_longitude], df[colum_latitude]))



#country sum of value
value_sum_per_country = gdf.groupby('region_id')['value'].sum().reset_index()

print(value_sum_per_country)

#country sum or normalized emission
#should be sum points of each country everwhere
norm_sum = gdf.groupby('region_id')['weight_norm'].sum().reset_index()
norm_sum['points'] = gdf.groupby('region_id').count().reset_index()['value']
print(norm_sum)

#
# #Check the total sum of value that gets distributed to the ROW countries
# #countries that are wthin WIOD 16
regions= ['AUS', 'AUT', 'BEL', 'BGR', 'BRA', 'CAN', 'CHE', 'CHN', 'CYP', 'CZE',
       'DEU', 'DNK', 'ESP', 'EST', 'FIN', 'FRA', 'GBR', 'GRC', 'HRV', 'HUN',
       'IDN', 'IND', 'IRL', 'ITA', 'JPN', 'KOR', 'LTU', 'LUX', 'LVA', 'MEX',
       'MLT', 'NLD', 'NOR', 'POL', 'PRT', 'ROU', 'RUS', 'SVK', 'SVN', 'SWE',
       'TUR', 'TWN', 'USA', 'ROW']
# #take out of the final matrix the total value that is assigned to the counrties
filtered_df = value_sum_per_country[['region_id', 'value']][~value_sum_per_country['region_id'].isin(regions)]
# #Sum all the ROW values
print(filtered_df['value'].sum())

# #check in the glob_prod (glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0]
# # (run debugger to get: the total value forestry: 88855.5801563 ), if the outcome matches, the total ROW value was assigned

# check how many points are considered as double weight i.e. near deforestation
count_of_2 = (df['weight'] == 2).sum()
print(count_of_2)