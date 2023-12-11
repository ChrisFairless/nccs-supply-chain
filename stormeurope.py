import pandas as pd
import numpy as np
import pycountry
from climada.util.api_client import Client
from climada.hazard import Hazard

WS_SCENARIO_LOOKUP = {
    'rcp26': 'ssp126',
    'rcp45': 'ssp245',
    'rcp60': 'ssp370',  # TODO check this is acceptable
    'rcp85': 'ssp585',
    'historical': 'None'
}
# Available scenarios: 'None' (historical), 'ssp126', 'ssp245', 'ssp370', 'ssp585'




def get_impf_set():
    return ImpactFuncSet(ImpfStormEurope.from_schwierz())


def get_hazard(scenario, country_iso3alpha, gcm_list=None):
    country_iso3num = int(pycountry.countries.get(alpha_3=country_iso3alpha).numeric)
    client = Client()

    era5 = get_era5()
    era5.centroids.set_lat_lon_to_meta()
    if scenario == 'observed':
        return era5.select(reg_id = country_iso3num)

    ws_scenario = WS_SCENARIO_LOOKUP[scenario]
    if not gcm_list:
        storm_df = get_cmip6_models([ws_scenario])
        gcm_list = storm_df['gcm']
    
    # Reproject each hazard dataset to match ERA5
    # This is super slow but it solves the problems of hazards being on different
    haz_list = [get_hazard_one_gcm(client, gcm, ws_scenario, country_iso3num, era5.centroids) for gcm in gcm_list]
    haz_list = [h for h in haz_list if h is not None]
    return Hazard.concat(haz_list)


def aggregate_windstorm_to_year(haz):
    dt = np.diff(haz.date)
    # Check the date ordinals behave as we'd expect
    assert(sum(abs(dt) < 100) / dt.size > 0.95)   # Vast majority of gaps between events are less than 100 days
    assert(max(dt) > 180)                         # But there are 6 month gaps (spring and summer)
    ix = abs(dt) > 180
    year_id = np.cumsum(ix)
    
    

def get_era5():
    client = Client()
    haz = client.get_hazard(
                'storm_europe',
                properties={
                    'spatial_coverage': 'Europe',
                    'data_source': 'ERA5',
                }
            )
    return haz


def get_hazard_one_gcm(client, gcm, ws_scenario, country_iso3num, regrid_centroids):
    haz = client.get_hazard(
        'storm_europe', properties={
            'spatial_coverage': 'Europe',
            'gcm': gcm,
            'climate_scenario': ws_scenario
        }
    )
    haz.centroids.set_lat_lon_to_meta()
    # Reproject to ERA5 with nearest neighbour resampling

    if True:
        haz = haz.change_centroids(regrid_centroids, threshold=500)  # FIXME use a more realistic threshold, this could dangerous if the edges of grids are in different places
    else:
        # I think this is a slower version of the above, but keeping this until I've checked properly
        haz.centroids.lat, haz.centroids.lon, haz.centroids.region_id = None, None, None
        haz.centroids.vars_check = haz.centroids.vars_check - {'lat', 'lon', 'region_id'}
        try:
            meta = regrid_centroids.meta
            haz.reproject_raster(transform = meta['transform'], width=meta['width'], height=meta['height'])
        except ValueError:
            # For now we are accepting errors in the meta...
            pass
        haz.centroids.set_meta_to_lat_lon()
        haz.centroids.set_region_id()
    haz = haz.select(reg_id = country_iso3num)
    return haz



def get_cmip6_models(scenario_list = None):
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
