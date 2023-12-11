import os
import geopandas as gpd
import shapely.geometry as geom
import shapely.vectorized
import numpy as np

_SHAPEFILE = gpd.read_file(os.path.dirname(__file__) + "/TM_WORLD_BORDERS-0.3.shp")


def get_country(lon, lat):
    ret = _SHAPEFILE.intersection(geom.Point(lon, lat))
    res = None
    for idx, r in enumerate(ret):
        if not r.is_empty:
            res = idx
            break
    if res is None:
        return None

    # return _SHAPEFILE.iloc[res].to_dict()
    return _SHAPEFILE.iloc[res]['ISO3']  # Return ISO3 code

def get_country_vectorized(coordinates):
    labels = np.zeros(len(coordinates), dtype=np.int8)
    for idx, country in _SHAPEFILE.iterrows():
        xs = np.array([c[0] for c in coordinates])
        ys = np.array([c[1] for c in coordinates])
        lbls = shapely.vectorized.contains(country.geometry, xs, ys)
        labels[lbls == True] = idx
    return [_SHAPEFILE.iloc[lbl].to_dict() for lbl in labels]

def get_country_vectorized_ISO(coordinates):
    iso3_codes = np.empty(len(coordinates), dtype=object)
    for idx, country in _SHAPEFILE.iterrows():
        xs = np.array([c[0] for c in coordinates])
        ys = np.array([c[1] for c in coordinates])
        lbls = shapely.vectorized.contains(country.geometry, xs, ys)
        iso3_codes[lbls] = country['ISO3']

    return iso3_codes.tolist()

def get_country_vectorized_name(coordinates):
    Name_codes = np.empty(len(coordinates), dtype=object)
    for idx, country in _SHAPEFILE.iterrows():
        xs = np.array([c[0] for c in coordinates])
        ys = np.array([c[1] for c in coordinates])
        lbls = shapely.vectorized.contains(country.geometry, xs, ys)
        Name_codes[lbls] = country['Name']

    return Name_codes.tolist()

# def

# all_points = [(random.uniform(-180, 180), random.uniform(-90, 90)) for _ in range(10000)]
# res = get_country_vectorized(all_points)

print(_SHAPEFILE.columns)

