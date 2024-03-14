import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.colors import Normalize

worldmap = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))

# file_list=["forestry_values_MRIO_avg(update)", "forestry_values_MRIO_avg(GDP)"]
#
#
# for file in file_list:
#     df = pd.read_hdf(f"data/{file}.h5")
#     colum_latitude = 'latitude'
#     column_longitude = 'longitude'
#     df[colum_latitude] = pd.to_numeric(df[colum_latitude], errors='coerce')
#     df[column_longitude] = pd.to_numeric(df[column_longitude], errors='coerce')
#     # Create a GeoDataFrame from the latitude and longitude columns
#     gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[column_longitude], df[colum_latitude]))
#     fig, ax = plt.subplots(figsize=(30, 12))
#     worldmap.plot(color="lightgrey", ax=ax)
#     sc = ax.scatter(gdf['longitude'], gdf['latitude'], c=gdf["value"], cmap='viridis', s=0.01)
#     # Add a colorbar
#     cbar = plt.colorbar(sc, ax=ax, label='Value')
#     # Set axis labels and title
#     ax.set_xlabel('Longitude')
#     ax.set_ylabel('Latitude')
#     ax.set_title(file+" MRIO value")
#     plt.savefig(f"data/{file}.png")


#
df = pd.read_hdf('data/forestry_values_MRIO_avg(WB-v2).h5')
colum_latitude = 'latitude'
column_longitude = 'longitude'
df[colum_latitude] = pd.to_numeric(df[colum_latitude], errors='coerce')
df[column_longitude] = pd.to_numeric(df[column_longitude], errors='coerce')
# Create a GeoDataFrame from the latitude and longitude columns
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[column_longitude], df[colum_latitude]))
#
# fig, ax = plt.subplots(figsize=(30, 12))
# worldmap.plot(color="lightgrey", ax=ax)
# # Use scatter to plot the points with color based on the 'value' column
# norm = Normalize(vmin=gdf['value'].min(), vmax=gdf['value'].mean())
# sc = ax.scatter(gdf['longitude'], gdf['latitude'], c=gdf['value'], cmap='viridis', norm=norm, s=0.01)
# # Add a colorbar
# cbar = plt.colorbar(sc, ax=ax, label='Value')
# # Set axis labels and title
# ax.set_xlabel('Longitude')
# ax.set_ylabel('Latitude')
# ax.set_title('Forestry Exposure with MRIO values in M.USD (WB production & deforestation)')
# # Show the plot
# plt.show()




#country sum of value
value_sum_per_country = df.groupby('region_id')['value'].sum().reset_index()
print(f"value_sum_per_country for forestry", value_sum_per_country)


#plot a barblot with this
# Plot the bar chart for the sum of values per country
# Sort the values and select the top 30
sorted_value_sum_per_country = value_sum_per_country.sort_values(by='value', ascending=False).head(30)

#Number of points per country
num_points_per_country = gdf.groupby('region_id').size()
# Sort the values and select the top 30
sorted_num_points_per_country = num_points_per_country.sort_values(ascending=False).head(30)


# Create a 2x2 grid of subplots
fig = plt.figure(figsize=(30, 18))
gs = GridSpec(2, 2, width_ratios=[2, 1])

# Plot the world map with scatter plot
ax0 = plt.subplot(gs[0, 0])
worldmap.plot(color="lightgrey", ax=ax0)
norm = Normalize(vmin=gdf['value'].min(), vmax=gdf['value'].mean())
sc = ax0.scatter(gdf['longitude'], gdf['latitude'], c=gdf['value'], cmap='cividis', norm=norm,
                 s=0.01)
cbar = plt.colorbar(sc, ax=ax0, label='Value')
ax0.set_xlabel('Longitude')
ax0.set_ylabel('Latitude')
ax0.set_title(f'Forestry Exposure with MRIO values scaled by Forestry and logging production in M.USD')

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
plt.show()