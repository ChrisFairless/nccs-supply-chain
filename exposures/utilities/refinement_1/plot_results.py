import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from matplotlib.colors import Normalize

worldmap = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
subscores = ["Subscore_energy", "Subscore_water", "Subscore_waste"]

# for subscore in subscores:
#     df = pd.read_hdf(f"data/{subscore}_ISO3_normalized.h5")
#
#     colum_latitude = 'latitude'
#     column_longitude = 'longitude'
#
#     df[colum_latitude] = pd.to_numeric(df[colum_latitude], errors='coerce')
#     df[column_longitude] = pd.to_numeric(df[column_longitude], errors='coerce')
#     # Create a GeoDataFrame from the latitude and longitude columns
#     gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[column_longitude], df[colum_latitude]))
#
#     fig, ax = plt.subplots(figsize=(30, 12))
#     worldmap.plot(color="lightgrey", ax=ax)
#
#     sc = ax.scatter(gdf['longitude'], gdf['latitude'], c=gdf["country_normalized"], cmap='viridis', s=0.01)
#     # Add a colorbar
#     cbar = plt.colorbar(sc, ax=ax, label='Value')
#     # Set axis labels and title
#     ax.set_xlabel('Longitude')
#     ax.set_ylabel('Latitude')
#
#     ax.set_title(subscore)
#
#     plt.savefig(f"data/{subscore}_cnormalized.png")


for subscore in subscores:
    df = pd.read_hdf(f"data/{subscore}_MRIO.h5")
    colum_latitude = 'latitude'
    column_longitude = 'longitude'
    df[colum_latitude] = pd.to_numeric(df[colum_latitude], errors='coerce')
    df[column_longitude] = pd.to_numeric(df[column_longitude], errors='coerce')
    # Create a GeoDataFrame from the latitude and longitude columns
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[column_longitude], df[colum_latitude]))
    fig, ax = plt.subplots(figsize=(30, 12))
    worldmap.plot(color="lightgrey", ax=ax)

    norm = Normalize(vmin=gdf['value'].min(), vmax=gdf['value'].mean())

    sc = ax.scatter(gdf['longitude'], gdf['latitude'], c=gdf["value"], cmap='viridis', norm=norm, s=0.01)
    # Add a colorbar
    cbar = plt.colorbar(sc, ax=ax, label='Value')
    # Set axis labels and title
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title(subscore+" MRIO value")
    plt.savefig(f"data/{subscore}_MRIO.png")

