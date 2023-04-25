import json
import logging

import numpy as np
import pandas as pd
import xyzservices.providers as xyz
from bokeh.io import curdoc
from bokeh.layouts import layout
from bokeh.models import ColumnDataSource, DataTable, Div, GeoJSONDataSource, LinearColorMapper, Patches, Select, \
    TableColumn
from bokeh.palettes import Viridis256
from bokeh.plotting import figure

with open("countries_wgs84.geojson", "r") as f:
    countries = json.load(f)
    COUNTRIES_BY_NAME = {c['properties']['ADMIN']: c for c in countries['features']}  # ISO_A3 would way safer

DS_INDIRECT_BASE = pd.read_csv("results/indirect_impacts.csv")
HAZARD_TYPES = DS_INDIRECT_BASE.hazard_type.unique()

selected_hazard_type = HAZARD_TYPES[0]
SELECTED_COUNTRY = None
SELECTED_SECTOR = None


def filter_data(ds: pd.DataFrame, imp_country=None, sector=None, hazard_type=None):
    if imp_country is not None:
        ds = ds[ds.country_of_impact == imp_country]
    if sector is not None:
        ds = ds[ds.sector == sector]
    if hazard_type is not None:
        ds = ds[ds.hazard_type == hazard_type]
    return ds


def get_country_source(ds, gj):
    result_countries = []
    sub = ds.groupby("country_of_impact")['value'].sum(numeric_only=True)
    for (country, summed) in sub.items():
        country_geom = gj.get(country, None)

        if country_geom is None:
            logging.warning(f"Could not find country {country}, omitting.")
            continue

        country_geom['properties']['value'] = summed
        result_countries.append(country_geom)
    return result_countries


def get_barplot_source(ds):
    data = ds.groupby("sector")['value'].sum(numeric_only=True)
    data = [(k, v) for k, v in sorted(data.items())]
    data = sorted(data, key=lambda x: x[1], reverse=True)

    sectors = [k[0][:50] for k in data]
    values = [k[1] for k in data]
    return dict(
        sectors=sectors,
        impact=values
    )


def to_gj_feature_collection(features):
    return json.dumps({"type": "FeatureCollection", "features": features})


def update_country_source(ds):
    new_data = get_country_source(ds, COUNTRIES_BY_NAME)
    geo_source.geojson = to_gj_feature_collection(new_data)


def update_barplot_source(ds):
    new_data = get_barplot_source(ds)
    source_barplot.data = new_data
    p_barpot.x_range.factors = source_barplot.data['sectors']


def update_plots(selected_imp_country, selected_sector, selected_hazard_type):
    update_country_source(filter_data(DS_INDIRECT_BASE, None, selected_sector, selected_hazard_type))
    update_barplot_source(filter_data(DS_INDIRECT_BASE, selected_imp_country, None, selected_hazard_type))


def on_country_selected(attr, old, new):
    global SELECTED_COUNTRY, SELECTED_SECTOR
    SELECTED_SECTOR = None
    if len(new) == 0:
        update_plots(
            selected_imp_country=None,
            selected_sector=None,
            selected_hazard_type=selected_hazard_type
        )
        SELECTED_COUNTRY = None
        return
    countries = json.loads(geo_source.geojson)['features'][new[0]]  # We should replace this to another lookup
    selected_imp_country = countries['properties']['ADMIN']
    SELECTED_COUNTRY = selected_imp_country
    update_plots(
        selected_imp_country=selected_imp_country,
        selected_sector=None,
        selected_hazard_type=selected_hazard_type
    )


def on_sector_selected(attr, old, new):
    global SELECTED_COUNTRY, SELECTED_SECTOR
    SELECTED_COUNTRY = None
    if len(new) == 0:
        update_plots(
            selected_imp_country=None,
            selected_sector=None,
            selected_hazard_type=selected_hazard_type
        )
        SELECTED_SECTOR = None
        return
    sector = source_barplot.data["sectors"][new[0]]  # We should replace this to another lookup
    SELECTED_SECTOR = sector
    update_plots(
        selected_imp_country=None,
        selected_sector=sector,
        selected_hazard_type=selected_hazard_type
    )


def on_hazard_type_changed(attr, old, new):
    global selected_hazard_type
    selected_hazard_type = new
    update_plots(
        selected_imp_country=SELECTED_COUNTRY,
        selected_sector=SELECTED_SECTOR,
        selected_hazard_type=selected_hazard_type
    )


logging.getLogger().setLevel(logging.INFO)

features = get_country_source(DS_INDIRECT_BASE, COUNTRIES_BY_NAME)
select_hazard_type = Select(title="Hazard Type", options=sorted(HAZARD_TYPES), value=selected_hazard_type, width=200)
select_hazard_type.on_change("value", on_hazard_type_changed)

# Country Plot
geo_source = GeoJSONDataSource(geojson=to_gj_feature_collection(features))
geo_source.selected.on_change('indices', on_country_selected)

p_countries = figure(
    title="Texas Unemployment, 2009",
    height=700, width=700,
    x_axis_type="mercator", y_axis_type="mercator",
    match_aspect=True,
    tools=["tap", "pan", "wheel_zoom"],
    tooltips=[
        ("Name", "@ADMIN"), ("Indirect Impact", "@value")
    ]
)
p_countries.add_tile(xyz.OpenStreetMap.Mapnik)
p_countries.grid.grid_line_color = None
p_countries.hover.point_policy = "follow_mouse"

color_mapper = LinearColorMapper(palette=Viridis256)
r = p_countries.patches(
    'xs', 'ys', source=geo_source,
    fill_color={'field': 'value', 'transform': color_mapper},
    fill_alpha=0.7, line_color="white", line_width=0.5
)
r.selection_glyph = Patches(
    line_color="blue", line_width=2.0, fill_color={'field': 'value', 'transform': color_mapper},
    fill_alpha=0.7
)
color_bar = r.construct_color_bar(
    padding=0
)
p_countries.add_layout(color_bar, 'below')

source_barplot = ColumnDataSource(get_barplot_source(DS_INDIRECT_BASE))
source_barplot.selected.on_change('indices', on_sector_selected)

p_barpot = figure(
    x_range=source_barplot.data['sectors'], height=700, width=1400,
    title=f"Expected total production impact for Switzerland", tools=["tap", "reset", "save"]
)

p_barpot.vbar(x="sectors", top="impact", width=0.9, source=source_barplot)
p_barpot.min_border_left = 200
p_barpot.y_range.start = 0
p_barpot.xaxis.major_label_orientation = np.pi / 4

# table
columns = [
    TableColumn(field="sectors", title="Sector"),
    TableColumn(field="impact", title="Indirect Impact"),
]

data_table = DataTable(source=source_barplot, columns=columns, height=400, width=400)
select_hazard_type.sizing_mode = "fixed"
lt = layout(
    [
        [select_hazard_type, Div(sizing_mode="stretch_width")],
        [p_countries, p_barpot],
        [data_table]
    ],
    sizing_mode="stretch_width"
)
curdoc().add_root(lt)
curdoc().title = "NCCS - Dashboard"
