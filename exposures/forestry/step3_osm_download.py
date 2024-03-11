
from pathlib import Path

from climada_petals.entity.exposures.openstreetmap.osm_dataloader import OSMRaw, OSMFileQuery
from climada import CONFIG
from climada_petals.util.constants import DICT_GEOFABRIK
import pandas as pd
import time
# timestr = time.strftime("%Y%m%d")

DATA_DIR = CONFIG.exposures.openstreetmap.local_data.dir()

iso3_list = list(DICT_GEOFABRIK.keys()) #  for all countries 192

#prior to running the code:
### RUSSIA (RUS-A and RUS-E) remove from the DICT_GEOFABRIK and were downloaded manually

for iso3 in iso3_list:
    gdfs = []
    OSMRaw().get_data_geofabrik(iso3, file_format='pbf', save_path=DATA_DIR)

    PLFileQuery = OSMFileQuery(Path(DATA_DIR, f'{DICT_GEOFABRIK[iso3][1]}-latest.osm.pbf'))
    osm_queries = ["boundary='national_park'", "boundary='protected_area'"] ### key to be updated as required
    for osm_query in osm_queries:
        osm_keys = ['boundary'] ### key to be updated as required

        gdf_forest = PLFileQuery.retrieve('multipolygons', osm_keys, osm_query)

        gdfs.append(gdf_forest)

    gdfs = pd.concat(gdfs)

    gdfs.to_file(f'data/{DICT_GEOFABRIK[iso3][1]}-nat-prot.geojson', driver='GeoJSON')