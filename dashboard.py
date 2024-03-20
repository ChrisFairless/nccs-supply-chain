import glob
import json
import logging
import os

import numpy as np
import pandas as pd
import xyzservices.providers as xyz
from bokeh.io import curdoc
from bokeh.layouts import layout
from bokeh.models import (
    ColumnDataSource, DataTable, Div, GeoJSONDataSource, LogColorMapper, Patches, Select,
    TabPanel, TableColumn, Tabs
)
from bokeh.plotting import figure

from utils.folder_naming import get_indirect_output_dir, get_resource_dir

"""
To run the dashboard.py 
first: run the the terminal the following command: python dashboard.py
next: bokeh serve dashboard.py --show
"""

RUN_TITLE = "best_guesstimate_22_01_2024"

with open(f"{get_resource_dir()}/countries_wgs84.geojson", "r") as f:
    countries = json.load(f)
    COUNTRIES_BY_NAME = {c['properties']['ISO_A3']: c for c in countries['features']}  # ISO_A3 would way safer

if not os.path.isfile("complete.csv"):
    data_files = glob.glob(f"{get_indirect_output_dir(RUN_TITLE)}/indirect_impacts_*.csv")
    dfs = []
    for filename in data_files:
        df = pd.read_csv(filename)
        df['country_of_impact_iso_a3'] = filename.split("_")[-1].split(".")[0]

        # TODO Hotfix to be removed, because there were no io approaches in the testing files
        if "leontief" in filename:
            df['io_approach'] = "leontief"
        else:
            df['io_approach'] = "ghosh"

        dfs.append(df)
    DS_INDIRECT_BASE = pd.concat(dfs)
    DS_INDIRECT_BASE.drop(columns=['Unnamed: 0'], inplace=True)
    DS_INDIRECT_BASE["ref_year"] = DS_INDIRECT_BASE["ref_year"].astype(str)
    DS_INDIRECT_BASE["value"] = DS_INDIRECT_BASE["iAAPL"].copy()
    # DS_INDIRECT_BASE["value"] = DS_INDIRECT_BASE["impact_aai"].copy() #TODO to be removed, old configurations,
    #  and used for best guesstimate run
    DS_INDIRECT_BASE['sector'] = [s[:50] for s in DS_INDIRECT_BASE['sector']]
    DS_INDIRECT_BASE.to_csv("complete.csv")
else:
    DS_INDIRECT_BASE = pd.read_csv("complete.csv")
    DS_INDIRECT_BASE.scenario = ['None' if pd.isna(s) else s for s in DS_INDIRECT_BASE.scenario]

HAZARD_TYPES = DS_INDIRECT_BASE.hazard_type.unique()
IMPACTED_SECTORS = DS_INDIRECT_BASE.sector_of_impact.unique()
METRICS = ["iAAPL", "irAAPL", "iPL100", "irPL100"]
# METRICS = ["impact_max", "imapct_max_%", "impact_aai", "rel_impact_aai_%","impact_rp_10", "rel_impact_rp_100_%"]
# #TODO to be removed, old configurations, and used for best guesstimate run
IO_APPROACH = DS_INDIRECT_BASE.io_approach.unique()
SCENARIOS = DS_INDIRECT_BASE.scenario.unique()
REF_YEARS = DS_INDIRECT_BASE.ref_year.unique()

# Defaults for the dropdowns when opening the dashboard
selected_hazard_type = HAZARD_TYPES[0]
selected_impacted_sector = IMPACTED_SECTORS[0]
selected_metric = METRICS[0]
selected_io_approach = IO_APPROACH[0]
selected_scenario = SCENARIOS[0]
selected_ref_year = REF_YEARS[0]

# Variables which hold the country and sector the user clicked on the map / barplot
SELECTED_COUNTRY = None  # The country which is shocked
SELECTED_SECTOR = None  # The sector which is indirectly impacted


def filter_data(
        ds: pd.DataFrame,
        imp_country=None,
        sector=None,
        hazard_type=None,
        sector_of_impact=None,
        scenario=None,
        ref_year=None,
        io_approach=None):
    if imp_country is not None:
        ds = ds[ds.country_of_impact_iso_a3 == imp_country]
    if sector_of_impact is not None:
        ds = ds[ds.sector_of_impact == sector_of_impact]
    if sector is not None:
        ds = ds[ds.sector == sector]
    if hazard_type is not None:
        ds = ds[ds.hazard_type == hazard_type]
    # TODO where is the metric filter?
    if scenario is not None:
        ds = ds[ds.scenario == scenario]
    if ref_year is not None:
        ds = ds[ds.ref_year == str(ref_year)]
    if io_approach is not None:
        ds = ds[ds.io_approach == io_approach]

    print(len(ds))
    return ds


def get_country_source(ds, gj):
    result_countries = []
    sub = ds.groupby("country_of_impact_iso_a3")['value'].sum(numeric_only=True)

    for (country, summed) in sub.items():
        country_geom = gj.get(country, None).copy()

        if country_geom is None:
            logging.warning(f"Could not find country {country}, omitting.")
            continue

        country_geom['properties']['value'] = summed
        result_countries.append(country_geom)

    sub = ds.groupby("country_of_impact")['value'].sum(numeric_only=True).reset_index()
    return result_countries, {"country": sub.country_of_impact, "impact": sub.value}


def get_barplot_source(ds):
    data = ds.groupby("sector")['value'].sum(numeric_only=True)
    data = [(k, v) for k, v in sorted(data.items())]
    data = sorted(data, key=lambda x: x[1], reverse=True)

    sectors = [k[0] for k in data]
    values = [k[1] for k in data]
    return dict(
        sectors=sectors,
        impact=values
    )


def to_gj_feature_collection(features):
    return json.dumps({"type": "FeatureCollection", "features": features})


def update_country_source(ds):
    new_data, table_data = get_country_source(ds, COUNTRIES_BY_NAME)
    geo_source.geojson = to_gj_feature_collection(new_data)
    country_table_source.data = table_data


def update_barplot_source(ds):
    new_data = get_barplot_source(ds)
    source_barplot.data = new_data
    p_barpot.x_range.factors = source_barplot.data['sectors']


def update_plots(
        selected_imp_country,
        selected_sector,
        selected_hazard_type,
        selected_impacted_sector,
        metric,  # TODO shouldn't it be selected_metric?
        selected_scenario,
        selected_ref_year,
        selected_io_approach):
    # TODO Find all update_plots calls and update them to use the new parameters
    DS_INDIRECT_BASE["value"] = DS_INDIRECT_BASE[metric]
    print(
        f"Updating plots with {selected_imp_country} {selected_sector} {selected_hazard_type} "
        f"{selected_impacted_sector} {metric} {selected_scenario} {selected_ref_year} {selected_io_approach}"
        # TODO can this stement be removed?
    )
    update_country_source(
        filter_data(
            ds=DS_INDIRECT_BASE,
            imp_country=None,
            sector=selected_sector,
            hazard_type=selected_hazard_type,
            sector_of_impact=selected_impacted_sector,
            # TODO where is the metric or selected_metric ?
            scenario=selected_scenario,
            ref_year=selected_ref_year,
            io_approach=selected_io_approach
        )
    )
    update_barplot_source(
        filter_data(
            ds=DS_INDIRECT_BASE,
            imp_country=selected_imp_country,
            sector=None,
            hazard_type=selected_hazard_type,
            sector_of_impact=selected_impacted_sector,
            # TODO where is the metric or selected_metric ?
            scenario=selected_scenario,
            ref_year=selected_ref_year,
            io_approach=selected_io_approach
        )
    )


def on_country_selected(attr, old, new):
    global SELECTED_COUNTRY, SELECTED_SECTOR
    SELECTED_SECTOR = None
    if len(new) == 0:
        update_plots(
            selected_imp_country=None,
            selected_sector=None,
            selected_hazard_type=selected_hazard_type,
            selected_impacted_sector=selected_impacted_sector,
            metric=selected_metric,  # TODO shouldn't it be selected_metric?
            selected_scenario=selected_scenario,
            selected_ref_year=selected_ref_year,
            selected_io_approach=selected_io_approach

        )
        SELECTED_COUNTRY = None
        return
    countries = json.loads(geo_source.geojson)['features'][new[0]]  # We should replace this to another lookup
    selected_imp_country = countries['properties']['ISO_A3']
    SELECTED_COUNTRY = selected_imp_country
    update_plots(
        selected_imp_country=selected_imp_country,
        selected_sector=None,
        selected_hazard_type=selected_hazard_type,
        selected_impacted_sector=selected_impacted_sector,
        metric=selected_metric,  # TODO shouldn't it be selected_metric?
        selected_scenario=selected_scenario,
        selected_ref_year=selected_ref_year,
        selected_io_approach=selected_io_approach
    )


def on_sector_selected(attr, old, new):
    global SELECTED_COUNTRY, SELECTED_SECTOR
    SELECTED_COUNTRY = None
    if len(new) == 0:
        update_plots(
            selected_imp_country=None,
            selected_sector=None,
            selected_hazard_type=selected_hazard_type,
            selected_impacted_sector=selected_impacted_sector,
            metric=selected_metric,  # TODO shouldn't it be selected_metric?
            selected_scenario=selected_scenario,
            selected_ref_year=selected_ref_year,
            selected_io_approach=selected_io_approach
        )
        SELECTED_SECTOR = None
        return
    sector = source_barplot.data["sectors"][new[0]]  # We should replace this to another lookup
    SELECTED_SECTOR = sector
    update_plots(
        selected_imp_country=None,
        selected_sector=sector,
        selected_hazard_type=selected_hazard_type,
        selected_impacted_sector=selected_impacted_sector,
        metric=selected_metric,  # TODO shouldn't it be selected_metric?
        selected_scenario=selected_scenario,
        selected_ref_year=selected_ref_year,
        selected_io_approach=selected_io_approach
    )


def on_hazard_type_changed(attr, old, new):
    global selected_hazard_type
    selected_hazard_type = new
    update_plots(
        selected_imp_country=SELECTED_COUNTRY,
        selected_sector=SELECTED_SECTOR,
        selected_hazard_type=selected_hazard_type,
        selected_impacted_sector=selected_impacted_sector,
        metric=selected_metric,  # TODO shouldn't it be selected_metric?
        selected_scenario=selected_scenario,
        selected_ref_year=selected_ref_year,
        selected_io_approach=selected_io_approach
    )


def on_impacted_sector_changed(attr, old, new):
    global selected_impacted_sector
    selected_impacted_sector = new
    update_plots(
        selected_imp_country=SELECTED_COUNTRY,
        selected_sector=SELECTED_SECTOR,
        selected_hazard_type=selected_hazard_type,
        selected_impacted_sector=selected_impacted_sector,
        metric=selected_metric,  # TODO shouldn't it be selected_metric?
        selected_scenario=selected_scenario,
        selected_ref_year=selected_ref_year,
        selected_io_approach=selected_io_approach
    )


def on_metric_changed(attr, old, new):
    global selected_metric
    selected_metric = new
    update_plots(
        selected_imp_country=SELECTED_COUNTRY,
        selected_sector=SELECTED_SECTOR,
        selected_hazard_type=selected_hazard_type,
        selected_impacted_sector=selected_impacted_sector,
        metric=selected_metric,  # TODO shouldn't it be selected_metric?
        selected_scenario=selected_scenario,
        selected_ref_year=selected_ref_year,
        selected_io_approach=selected_io_approach
    )


def on_scenario_changed(attr, old, new):
    global selected_scenario
    selected_scenario = new
    update_plots(
        selected_imp_country=SELECTED_COUNTRY,
        selected_sector=SELECTED_SECTOR,
        selected_hazard_type=selected_hazard_type,
        selected_impacted_sector=selected_impacted_sector,
        metric=selected_metric,  # TODO shouldn't it be selected_metric?
        selected_scenario=selected_scenario,
        selected_ref_year=selected_ref_year,
        selected_io_approach=selected_io_approach
    )


def on_ref_year_changed(attr, old, new):
    global selected_ref_year
    selected_ref_year = new
    update_plots(
        selected_imp_country=SELECTED_COUNTRY,
        selected_sector=SELECTED_SECTOR,
        selected_hazard_type=selected_hazard_type,
        selected_impacted_sector=selected_impacted_sector,
        metric=selected_metric,  # TODO shouldn't it be selected_metric?
        selected_scenario=selected_scenario,
        selected_ref_year=selected_ref_year,
        selected_io_approach=selected_io_approach
    )


def on_io_approach_changed(attr, old, new):
    global selected_io_approach
    selected_io_approach = new
    update_plots(
        selected_imp_country=SELECTED_COUNTRY,
        selected_sector=SELECTED_SECTOR,
        selected_hazard_type=selected_hazard_type,
        selected_impacted_sector=selected_impacted_sector,
        metric=selected_metric,  # TODO shouldn't it be selected_metric?
        selected_scenario=selected_scenario,
        selected_ref_year=selected_ref_year,
        selected_io_approach=selected_io_approach
    )


# logging.getLogger().setLevel(logging.INFO)

# Buttons for selection

select_hazard_type = Select(
    title="Hazard Type",
    options=sorted(HAZARD_TYPES),
    value=selected_hazard_type,
    width=200
)
select_hazard_type.on_change("value", on_hazard_type_changed)

select_source_sector = Select(
    title="Impacted Sector",
    options=sorted(IMPACTED_SECTORS),
    value=selected_impacted_sector,
    width=200
)
select_source_sector.on_change("value", on_impacted_sector_changed)
select_source_sector.sizing_mode = "fixed"

select_metric = Select(
    title="Metric",
    options=sorted(METRICS),
    value=selected_metric,
    width=200
)
select_metric.on_change("value", on_metric_changed)
select_metric.sizing_mode = "fixed"

select_scenario = Select(
    title="Scenario",
    options=sorted(SCENARIOS),
    value=selected_scenario,
    width=200
)
select_scenario.on_change("value", on_scenario_changed)
select_scenario.sizing_mode = "fixed"

select_ref_year = Select(
    title="Year",
    options=sorted(REF_YEARS),
    value=selected_ref_year,
    width=200
)
select_ref_year.on_change("value", on_ref_year_changed)
select_ref_year.sizing_mode = "fixed"

select_io_approach = Select(
    title="IO Approach",
    options=sorted(IO_APPROACH),
    value=selected_io_approach,
    width=200
)
select_io_approach.on_change("value", on_io_approach_changed)
select_io_approach.sizing_mode = "fixed"

# Country Plot
# This is for the country, value table

features, country_table_data = get_country_source(DS_INDIRECT_BASE, COUNTRIES_BY_NAME)
geo_source = GeoJSONDataSource(geojson=to_gj_feature_collection(features))
geo_source.selected.on_change('indices', on_country_selected)
country_table_source = ColumnDataSource(country_table_data)

p_countries = figure(
    title="Indirect impact contribution by country",
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

color_mapper = LogColorMapper(palette="Sunset11", low=1, high=None)
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

data_table_sector = DataTable(source=source_barplot, columns=columns, height=400, width=400)
select_hazard_type.sizing_mode = "fixed"

columns = [
    TableColumn(field="country", title="Country"),
    TableColumn(field="impact", title="Indirect Impact"),
]

data_table_country = DataTable(source=country_table_source, columns=columns, height=400, width=400)
select_hazard_type.sizing_mode = "fixed"

tab = Tabs(
    tabs=[TabPanel(child=data_table_sector, title="Sectors"), TabPanel(child=data_table_country, title="Countries")]
)

lt = layout(
    [
        [select_hazard_type, select_source_sector, select_metric, select_scenario, select_ref_year, select_io_approach,
         Div(sizing_mode="stretch_width")],
        # TODO Add the new buttons here  select_scenario, select_ref_year,select_io_approach
        [p_countries, p_barpot],
        [tab]
    ],
    sizing_mode="stretch_width"
)
curdoc().add_root(lt)
curdoc().title = "NCCS - Dashboard"
print("Done!\nTo show the Dashboard run:\nbokeh serve dashboard.py --show")
