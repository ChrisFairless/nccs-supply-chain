import pandas as pd
import numpy as np
import pycountry
import copy
import os
from pathlib import Path
from scipy import sparse
import climada.util.coordinates as u_coord
from climada.util.api_client import Client
from climada.hazard import Hazard
from climada.entity import ImpactFuncSet
from climada.entity.impact_funcs.storm_europe import ImpfStormEurope
from utils.s3client import download_from_s3_bucket

WS_SCENARIO_LOOKUP = {
    'rcp26': 'ssp126',
    'rcp45': 'ssp245',
    'rcp60': 'ssp370',  # TODO check this is an acceptable approximation
    'rcp85': 'ssp585',
    'historical': 'None',
    'None': 'None',
    'observed': 'observed'
}
# Available scenarios: 'None' (historical), 'ssp126', 'ssp245', 'ssp370', 'ssp585'

DEFAULT_DATA_DIR = Path('resources', 'hazard', 'stormeurope', 'data')


def get_impf_set():
    return ImpactFuncSet(ImpfStormEurope.from_schwierz())


def download_hazard_from_s3(scenario, country_iso3alpha, save_dir=DEFAULT_DATA_DIR):
    country_iso3num = str(pycountry.countries.get(alpha_3=country_iso3alpha).numeric)
    s3_filepath = f'stormeurope_hazard/stormeurope_{scenario}_{country_iso3num}.hdf5' #replaced old statement
    outputfile=f'{save_dir}/stormeurope_{scenario}_{country_iso3num}.hdf5'

    download_from_s3_bucket(s3_filepath, outputfile)


def get_hazard(scenario, country_iso3alpha, save_dir=DEFAULT_DATA_DIR):
    country_iso3num = str(pycountry.countries.get(alpha_3=country_iso3alpha).numeric) #changed here
    if scenario == "observed":
        return get_era5(country_iso3num)
    cmip_scenario = WS_SCENARIO_LOOKUP[scenario]
    filename = f'stormeurope_{cmip_scenario}_{country_iso3num}.hdf5'
    if not os.path.isfile(filename):
        download_hazard_from_s3(cmip_scenario, country_iso3alpha, save_dir)
        filename = f'{save_dir}/stormeurope_{scenario}_{country_iso3num}.hdf5' #inserted because otherwise file could not be opened
    return Hazard.from_hdf5(filename)


def get_era5(country_iso3num = None):
    client = Client()
    haz = client.get_hazard(
                'storm_europe',
                properties={
                    'spatial_coverage': 'Europe',
                    'data_source': 'ERA5',
                }
            )
    haz.centroids.set_lat_lon_to_meta()
    if country_iso3num:
        haz = subset_to_countries(haz, [country_iso3num])[country_iso3num]
    return haz


def get_raw_hazard_from_climada_api_one_gcm(client, gcm, ws_scenario):
    haz = client.get_hazard(
        'storm_europe', properties={
            'spatial_coverage': 'Europe',
            'gcm': gcm,
            'climate_scenario': ws_scenario
        }
    )
    haz.centroids.set_lat_lon_to_meta()
    return haz


def aggregate_windstorm_by_year(haz):
    dt = np.diff(haz.date)
    # years = [datetime.datetime.from_ordinal(d).year for d in haz.date]
    # dy = np.diff(years)
    ix_list = np.where(abs(dt) > 180)[0]
    ix_list = np.concatenate((
        np.array([0]),
        ix_list,
        np.array([len(haz.date) - 1])
    ))
    date_list = haz.date[ix_list]
    n_years = len(date_list) - 1
    event_frequency = 1 / n_years   # This could take a different value: we're effectively weighting all models equally with this
                                    # Although now that I think about it, I think every model has 30 years of events so it doesn't matter
                                    # And we'll re-assign the frequency once we concatenate all the models anyway...

    out_haz = Hazard.concat(
        [
            Hazard(
                haz_type = haz.haz_type,
                units = haz.units,
                centroids = haz.centroids,
                event_id = np.array([i]),
                frequency = np.array([event_frequency]),
                frequency_unit = "1/year",
                date = np.array([date_list[i]]),    # First event of the season, should probably be the first day of the season but we might never use it
                intensity = sparse.csr_matrix(
                    np.max(haz.intensity[start:stop, ], axis=0) #.toarray().transpose()
                )
            )
            for i, (start, stop) in enumerate(zip(ix_list[:-1], ix_list[1:]))
        ]
    )

    # validate
    assert(np.mod(len(out_haz.event_id), 30) == 0)
    assert(np.max(haz.intensity) == np.max(out_haz.intensity))
    # TODO more!

    return out_haz


def change_centroids_for_real_screw_you_climada(haz, centroids, threshold):

    # define empty hazard
    haz_new_cent = copy.deepcopy(haz)
    haz_new_cent.centroids = centroids

    new_cent_idx = u_coord.match_coordinates(
        haz.centroids.coord, centroids.coord, threshold=threshold
    )
    new_cent_reverse_idx = u_coord.match_coordinates(
        centroids.coord, haz.centroids.coord, threshold=threshold
    )
    if -1 in new_cent_reverse_idx:
        raise ValueError(
            "At least one hazard centroid is at a larger distance than the given threshold"
            f" {threshold} from the given centroids. Please choose a larger threshold or"
            " enlarge the centroids"
        )

    # re-assign attributes intensity and fraction
    for attr_name in ["intensity", "fraction"]:
        matrix = getattr(haz, attr_name)
        new_matrix = np.zeros_like(np.asmatrix(matrix.A))
        # TODO speed this up, there's a neat linear algebra way to do this
        new_matrix = sparse.csr_matrix(np.matrix(np.array([np.array([matrix.A[i, new_cent_reverse_idx]]) for i in range(matrix.shape[0])])))
        setattr(haz_new_cent, attr_name, new_matrix)
        # setattr(haz_new_cent, attr_name,
        #         sparse.csr_matrix(
        #             (matrix.data, new_cent_reverse_idx[matrix.indices], matrix.indptr),
        #             shape=(matrix.shape[0], centroids.size)
        #         ))

    return haz_new_cent


def regrid(haz, regrid_centroids, threshold=50):
    if not haz.centroids.meta or len(haz.centroids.meta) == 0:
        haz.centroids.set_lat_lon_to_meta()
    if True:
        # FIXME I prefer this option (nearest-neighbour regridding) but it's giving bad results and I don't have time to fix it
        # haz = haz.change_centroids(regrid_centroids, threshold=50)  # FIXME use a more realistic threshold, this could dangerous if the edges of grids are in different places
        haz = change_centroids_for_real_screw_you_climada(haz, regrid_centroids, threshold=threshold)
    else:
        # 
        # haz.centroids.lat, haz.centroids.lon, haz.centroids.region_id = None, None, None
        # haz.centroids.vars_check = haz.centroids.vars_check - {'lat', 'lon', 'region_id'}
        try:
            meta = regrid_centroids.meta
            haz.reproject_raster(transform = meta['transform'], width=meta['width'], height=meta['height'])
            haz.centroids.set_meta_to_lat_lon()
        except ValueError as e:
            print("Error in reprojection. Skipping: " + str(e))
            # For now we are accepting errors in the meta...
            pass
    if regrid_centroids.region_id is not None:
        haz.centroids.set_region_id()
    return haz


# We don't just subset to centroids with the country's region ID because sometimes a location's nearest centroid is
# across the border. Instead subset to a bounding box a little larger than the country + grid spacing, BUT dropping 
# all centroids over the ocean. The reasoning is that exposures close to a border should be able to map to hazard 
# across the border if its centroid is closer than the hazard centroids within the country, with the exception of 
# hazard centroids over the ocean, since wind speeds tend to be much much higher over open water and we'd rather map to
# one over land even if it's a little further away.
def subset_to_countries(haz, country_iso3num_list = None, buffer = 0.6):
    if not country_iso3num_list:
        country_iso3num_list = []
    if isinstance(country_iso3num_list, int):
        country_iso3num_list = [country_iso3num_list]
    if not isinstance(country_iso3num_list, list):
        raise ValueError('Please provide an integer or list of integers as country IDs in parameter country_iso3num_list')

    if len(country_iso3num_list) == 0:
        country_iso3num_list = np.unique(haz.centroids.region_id)
    
    haz_list = {
        country_iso3num: _subset_one_country(
            haz = haz,
            reg_id = country_iso3num,
            buffer = buffer
        ) for country_iso3num in country_iso3num_list
    }
    return haz_list


def _subset_one_country(haz, reg_id, buffer):
    region_ids = [x for x in np.unique(haz.centroids.region_id) if x != 0]
    haz_country = haz.select(reg_id = reg_id)
    extent = u_coord.latlon_bounds(haz_country.centroids.lat, haz_country.centroids.lon, buffer=buffer)
    haz_out = haz.select(extent = (extent[0], extent[2], extent[1], extent[3]))
    haz_out = haz_out.select(reg_id = region_ids)  # Remove coastal grid cells. Controversial but I think it's worth not including them
    # haz_out.centroids.set_lat_lon_to_meta()
    if haz_out.centroids.size == 0:
        raise ValueError(f'No centroids found over land for this location: {reg_id}')
    return haz_out


def get_cmip6_model_list(scenario_list = None):
    client = Client()
    # Get metadata for all the CMIP6 data on the API
    info_df = client.list_dataset_infos(data_type='storm_europe')
    info_df = pd.DataFrame(info_df)
    ix = [dat['data_source'] == 'CMIP6' and status == 'active' for dat, status in zip(info_df['properties'], info_df['status'])]
    info_df = info_df.loc[ix, ].reset_index()
    # Confirm there's still only one version of the data on the API
    versions_list = np.unique(info_df['version'])
    if not len(versions_list) == 1:
        Warning('It looks like there is now more than one version of the storm_europe data. Update the code to filter to choose the best version. For now using v1')
        info_df = info_df.loc[info_df['version'] == 'v1', ].reset_index()

    # Unnest the 'properties' column
    properties = pd.DataFrame([row for row in info_df['properties']])
    extra_info_cols = ['uuid', 'name', 'version', 'status', 'files']
    properties[extra_info_cols] = info_df[extra_info_cols]

    # Filter to models that have data for all desired scenarios
    if scenario_list:
        ws_scenario_list = [WS_SCENARIO_LOOKUP[s] if s in WS_SCENARIO_LOOKUP.keys() else s for s in scenario_list]
        ix = [scen in ws_scenario_list for scen in properties['climate_scenario']]
        properties = properties.loc[ix, ].reset_index()
        model_count = properties[['climate_scenario', 'gcm']]\
            .groupby(['gcm'])['gcm']\
            .count()
        gcm_list = np.array(model_count[model_count == len(scenario_list)].index)
        if len(gcm_list) == 0:
            raise ValueError(f'No models found for the requested scenarios: {ws_scenario_list}')
    else:
        gcm_list = np.unique(properties['gcm'])   

    ix = [gcm in gcm_list for gcm in properties['gcm']]
    properties = properties.loc[ix, ].reset_index()
    return properties
