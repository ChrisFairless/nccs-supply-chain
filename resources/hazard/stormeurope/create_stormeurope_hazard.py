import numpy as np
import os
import datetime
from climada.util.api_client import Client
from climada.hazard import Hazard
import glob
from pathlib import Path    

import pipeline.direct.stormeurope as stormeurope
from utils.s3client import upload_to_s3_bucket

# Script to generate stormeurope data

# The files here are big and can't all be stored locally, so we want to come up 
# with a way to save as much disk space as possible while we do the calculations

# Outermost element of the loop has to be the GCM: we want to download the data
# for it, extract and save everything we need and delete it

# Let's define a function that downloads something and deletes it when we're done:

working_dir = Path('.', 'resources', 'hazard', 'storm_europe', 'data')

if not os.path.exists(working_dir):
    raise NotADirectoryError(f'Create a working directory at {working_dir} before you start. Temporary output will go here')

gcm_all_df = stormeurope.get_cmip6_model_list()
gcm_all_df = gcm_all_df[gcm_all_df['status'] == 'active']
scenario_list = ['None', 'ssp126', 'ssp585']    # See stormeurope.py for available scenarios
country_iso3num_list = None  # Choose automatically

client = Client()
era5 = stormeurope.get_era5()

# centroids have been refactored and these checks don't work any more...
# assert(era5.centroids.meta['transform'][0] == 0.5)
# assert(era5.centroids.meta['transform'][4] == 0.5)

era5_by_country = stormeurope.subset_to_countries(era5)

client = Client(cache_enabled = None)  # Don't store downloaded files or we'll run out of memory fast

# plot ERA5 and write to hdf5
if False:
    plt = era5.plot_intensity(event=0)
    plt.figure.savefig(Path(working_dir, 'temp_' + 'era5' + '_' + 'ALL' + '.png'))
    era5.write_hdf5(Path(working_dir, 'temp_era5_ALL.hdf5'))

# Plot ERA5 by country
if False:
    for country in era5_by_country.keys():
        try:
            plt = era5_by_country[country].plot_intensity(event=0)
            plt.figure.savefig(Path(working_dir, 'temp_' + 'era5' + '_' + str(country) + '.png'))
            plt = era5_by_country[country].centroids.plot()
            plt.figure.savefig(Path(working_dir, 'temp_' + 'era5' + '_centroids_' + str(country) + '.png'))
        except:
            print("Couldn't do country " + str(country))

for scenario in scenario_list:
    print(f"\n*** WORKING ON SCENARIO {scenario} ***")
    gcm_scenario_df = gcm_all_df[gcm_all_df['climate_scenario'] == scenario]
    gcm_list = np.unique(gcm_scenario_df['gcm'])
    for i, gcm in enumerate(gcm_list):
        print(f"\nMODEL {i+1}/{len(gcm_list)}: {gcm}")
        print("Getting hazard")
        try:
            # FIXME my hacky regrid doesn't work with the latest version of CLIMADA which has refactored centroids 
            haz = stormeurope.get_raw_hazard_from_climada_api_one_gcm(client, gcm, scenario)
            haz = stormeurope.aggregate_windstorm_by_year(haz)
            d_lon = haz.centroids.meta['transform'][0]
            d_lat = haz.centroids.meta['transform'][4]
            # if not (d_lon == 0.5 and d_lat == 0.5):
            if not (haz.centroids == era5.centroids):
                print(f"Regridding from {d_lon} x {d_lat} grid to 0.5 x 0.5 grid")
                # FIXME this doesn't seem to be working right now? The Hazard.concat gives a message suggesting the centroids are different
                haz = stormeurope.regrid(haz, era5.centroids, threshold = 200)
            stormeurope.set_frequencies(all_equal=True)
            print("Splitting to countries")
            # FIXME I think this will miss countries too small to have their own centroid
            haz_by_country = stormeurope.subset_to_countries(haz)
            print("Saving")
            for country in haz_by_country.keys():  #TODO really this should be the countries in era5: it's an error if after regridding there are no points for it
                if country != 0:
                    filename = 'temp_' + scenario + '_' + gcm + '_' + str(country) + '.hdf5'
                    haz_by_country[country].write_hdf5(Path(working_dir, filename))
        except Exception as e:
            print("That didn't work. Skipping because we're in a rush")
            print(e)
            
        # TODO investigate: it could be faster to split into countries and _then_ regrid.
        if False:
            plt = haz.plot_intensity(event=0)
            plt.figure.savefig(Path(working_dir, 'temp_' + scenario + '_' + gcm + '_' + 'ALL' + '.png'))
            for country in haz_by_country.keys():
                if len(haz_by_country[country].centroids.lon) > 1:
                    plt = haz_by_country[country].plot_intensity(event=0)
                    plt.figure.savefig(Path(working_dir, 'temp_' + scenario + '_' + gcm + '_' + str(country) + '.png'))
                else:
                    print("Country is a single centroid: can't plot: " + str(country))
    
    # Aggregate each country's hazard:
    # for scenario in scenario_list:
    for country in era5_by_country.keys():
        if country != 0:
            filename_list = ['temp_' + scenario + '_' + gcm + '_' + str(country) + '.hdf5' for gcm in gcm_list]
            haz = Hazard.concat([Hazard.from_hdf5(f) for f in filename_list if os.path.isfile(f)])
            filename_combined_out = 'stormeurope_' + scenario + '_' + str(country) + '.hdf5'
            haz.write_hdf5(Path(working_dir, filename_combined_out))
            # if True:
            #     plt = haz.plot_intensity(event=0)
            #     plt.figure.savefig(Path(working_dir, 'stormeurope_' + scenario + '_' + str(country) + '.png'))
            [os.remove(Path(working_dir, f)) for f in filename_list if os.path.isfile(Path(working_dir, f))]
    
    # Clear up intermediate files
    # TODO!

# Upload to S3
if True:
    files_to_sync = glob.glob(Path(working_dir, 'stormeurope_*.hdf5'))

    for f in files_to_sync:
        print(f)
        # bucket_file = os.path.relpath(f, os.path.dirname(__file__)).replace("\\", "/")
        bucket_file = "stormeurope_hazard/" + f
        upload_to_s3_bucket(f, bucket_file)