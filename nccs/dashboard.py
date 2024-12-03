import glob
import json
import logging
from dataclasses import dataclass
from typing import List, Union

import numpy as np
import dotenv
import pandas as pd
import xyzservices.providers as xyz
from bokeh.io import curdoc
from bokeh.layouts import layout
from bokeh.models import (
    Button, ColumnDataSource, DataTable, Div, GeoJSONDataSource, LogColorMapper, Patches, Select, TabPanel, TableColumn,
    Tabs
)
from bokeh.plotting import figure

import nccs.utils.folder_naming
from nccs.utils.folder_naming import get_resources_dir
from nccs.utils.s3client import download_complete_csvs_to_results

logging.getLogger().setLevel(logging.INFO)

dotenv.load_dotenv()
"""
To run the nccs\dashboard.py 
first: run the the terminal the following command: python dashboard.py
next: bokeh serve nccs\dashboard.py --show
"""


@dataclass
class DashboardState:
    run_title: str
    file_path: str

    hazard_types: List[str]
    impacted_sectors: List[str]
    metrics: List[str]
    io_approaches: List[str]
    scenarios: List[str]
    ref_years: List[str]

    selected_hazard_type: str
    selected_impacted_sector: str
    selected_metric: str
    selected_io_approach: str
    selected_scenario: str
    selected_ref_year: str

    # these are only set after the data is loaded
    df: Union[pd.DataFrame, None] = None
    curr_view: Union[pd.DataFrame, None] = None

    selected_country: Union[str, None] = None
    selected_sector: Union[str, None] = None

    def select_country(self, country):
        self.selected_country = country
        self.curr_view = self._base_filter_data()
        self.update_plots()

    def select_sector(self, sector):
        self.selected_sector = sector
        self.update_plots()

    def select_hazard_type(self, hazard_type):
        self.selected_hazard_type = hazard_type
        self.update_plots()

    def select_impacted_sector(self, impacted_sector):
        self.selected_impacted_sector = impacted_sector
        self.update_plots()

    def select_metric(self, metric):
        self.selected_metric = metric
        self.update_plots()

    def select_scenario(self, scenario):
        self.selected_scenario = scenario
        self.update_plots()

    def select_ref_year(self, ref_year):
        self.selected_ref_year = ref_year
        self.update_plots()

    def select_io_approach(self, io_approach):
        self.selected_io_approach = io_approach
        self.update_plots()

    def load_data(self):
        self.df = pd.read_csv(self.file_path).replace({np.nan: None})
        self.df['value'] = self.df[self.selected_metric]
        self.update_plots()

    def update_plots(self):
        self.df['value'] = self.df[self.selected_metric]
        self.curr_view = self._base_filter_data()
        self.update_filter_options()
        try:
            self._update_country_source(self.curr_view)
            self._update_barplot_source(self.curr_view)
        except NameError as e:
            logging.error(f"Error updating plots: {e}")

    def update_filter_options(self):
        print("Updating filter options")
        select_hazard_type.options = sorted(self.hazard_types)
        select_source_sector.options = sorted(self.impacted_sectors)
        select_io_approach.options = sorted(self.io_approaches)

        try:
            df_haz = self.df[self.df.hazard_type == self.selected_hazard_type]
            selected_ref_year_options = df_haz.ref_year.unique()
            selected_ref_year_options = sorted([str(e) for e in selected_ref_year_options])
            select_ref_year.options = selected_ref_year_options
            select_ref_year.value = self.selected_ref_year if self.selected_ref_year in selected_ref_year_options else \
                selected_ref_year_options[0]

            selected_scenario_options = df_haz.scenario.unique()
            selected_scenario_options = sorted([str(e) for e in selected_scenario_options])
            select_scenario.options = selected_scenario_options
            select_scenario.value = self.selected_scenario if self.selected_scenario in selected_scenario_options else \
                selected_scenario_options[0]
        except Exception as e:
            logging.error(f"Error updating filter options: {e}")

    def _base_filter_data(self):
        ds = self.df

        if self.selected_io_approach is not None:
            ds = ds[ds.io_approach == self.selected_io_approach]
        if self.selected_hazard_type is not None:
            ds = ds[ds.hazard_type == self.selected_hazard_type]
        if self.selected_ref_year is not None:
            ds = ds[ds.ref_year.astype(str) == str(self.selected_ref_year)]
        if self.selected_scenario is not None:
            ds = ds[ds.scenario.astype(str) == str(self.selected_scenario)]
        if self.selected_impacted_sector is not None:
            ds = ds[ds.sector_of_impact == self.selected_impacted_sector]

        return ds

    def _update_country_source(self, ds: pd.DataFrame):
        global geo_source, country_table_source
        if self.selected_sector is not None:
            ds = ds[ds.sector == self.selected_sector]
        new_data, table_data = get_country_source(ds, COUNTRIES_BY_NAME)
        if geo_source is None:
            geo_source = GeoJSONDataSource(geojson=to_gj_feature_collection(new_data))
            geo_source.selected.on_change('indices', on_country_selected)
            country_table_source = ColumnDataSource(table_data)
        else:
            geo_source.geojson = to_gj_feature_collection(new_data)
            country_table_source.data = table_data

    def _update_barplot_source(self, ds: pd.DataFrame):
        global source_barplot
        if self.selected_country is not None:
            ds = ds[ds.country_of_impact_iso_a3 == self.selected_country]

        new_data = get_barplot_source(ds)
        if source_barplot is None:
            source_barplot = ColumnDataSource(new_data)
            source_barplot.selected.on_change('indices', on_sector_selected)
        else:
            source_barplot.data = new_data
            p_barpot.y_range.factors = source_barplot.data['sectors'][::-1]


def generate_dataset_state(input_file: str, run_title: str):
    df_indirect_base = pd.read_csv(input_file).replace({np.nan: None})

    hazard_types = [str(e) for e in df_indirect_base.hazard_type.unique()]
    impacted_sectors = [str(e) for e in df_indirect_base.sector_of_impact.unique()]
    metrics = ["iAAPL", "irAAPL", "iPL100", "irPL100"]
    io_approaches = [str(e) for e in df_indirect_base.io_approach.unique()]
    scenarios = [str(e) for e in df_indirect_base.scenario.unique()]
    ref_years = [str(e) for e in df_indirect_base.ref_year.unique()]

    state = DashboardState(
        run_title=run_title,
        file_path=input_file,
        df=None,
        curr_view=None,
        hazard_types=hazard_types,
        impacted_sectors=impacted_sectors,
        metrics=metrics,
        io_approaches=io_approaches,
        scenarios=scenarios,
        ref_years=ref_years,
        selected_hazard_type=hazard_types[0],
        selected_impacted_sector=impacted_sectors[0],
        selected_metric=metrics[0],
        selected_io_approach=io_approaches[0],
        selected_scenario=scenarios[0],
        selected_ref_year=ref_years[0],
        selected_country=None,
        selected_sector=None
    )
    return state


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
    if len(features) == 0:
        # we add four points to make the map show something
        features = [
            {"type": "Feature", "properties": {"value": 1}, "geometry": {"type": "Point", "coordinates": [-90, -180]}},
            {"type": "Feature", "properties": {"value": 1}, "geometry": {"type": "Point", "coordinates": [90, 180]}},
        ]
    return json.dumps({"type": "FeatureCollection", "features": features})


def on_country_selected(attr, old, new):
    global CURRENT_STATE
    new = json.loads(geo_source.geojson)['features'][new[0]]['properties']['ISO_A3'] if new else None
    CURRENT_STATE.select_country(new)


def on_sector_selected(attr, old, new):
    global CURRENT_STATE
    new = source_barplot.data["sectors"][new[0]] if new else None
    CURRENT_STATE.select_sector(new)


def on_run_changed(attr, old, new):
    global CURRENT_STATE
    CURRENT_STATE = STATES[new]
    CURRENT_STATE.load_data()


def on_hazard_type_changed(attr, old, new):
    global CURRENT_STATE
    CURRENT_STATE.select_hazard_type(new)


def on_impacted_sector_changed(attr, old, new):
    global CURRENT_STATE
    CURRENT_STATE.select_impacted_sector(new)


def on_metric_changed(attr, old, new):
    global CURRENT_STATE
    CURRENT_STATE.select_metric(new)


def on_scenario_changed(attr, old, new):
    global CURRENT_STATE
    CURRENT_STATE.select_scenario(new)


def on_ref_year_changed(attr, old, new):
    global CURRENT_STATE
    CURRENT_STATE.select_ref_year(new)


def on_io_approach_changed(attr, old, new):
    global CURRENT_STATE
    CURRENT_STATE.select_io_approach(new)


def update_state():
    global CURRENT_STATE
    global STATES

    logging.info("Updating state")
    if CURRENT_STATE:
        CURRENT_STATE.select_hazard_type("some-nonexistent-hazard")  # Crash the dashboard while loading the data

    CURRENT_STATE = None
    STATES = {}

    # Download the latest data
    try:
        download_complete_csvs_to_results()
    except Exception as e:
        logging.error(f"Error downloading data: {e}")

    # Load the data
    for file in glob.glob(f"{nccs.utils.folder_naming.get_output_dir()}/**/indirect/complete.csv"):
        run = file.replace("\\", "/").split("/")[-3]
        state = generate_dataset_state(file, run)
        logging.info(f"Loaded state for run {run} from {file}")
        STATES[run] = state
        if CURRENT_STATE is None:
            CURRENT_STATE = state
    try:
        CURRENT_STATE.load_data()
    except Exception as e:
        logging.error(f"Error loading data: {e}. This is probably because it's startup")


# Collect the country geometries
with open(f"{get_resources_dir()}/countries_wgs84.geojson", "r") as f:
    countries = json.load(f)
    COUNTRIES_BY_NAME = {c['properties']['ISO_A3']: c for c in countries['features']}  # ISO_A3 would way safer

# Get all complete.csv from the each run$
STATES = {}
CURRENT_STATE = None

update_state()

# Buttons for selection
select_run = Select(
    title="Pipeline Run",
    options=sorted(list(STATES.keys())),
    value=CURRENT_STATE.run_title,
    width=200
)
select_run.on_change("value", on_run_changed)

select_hazard_type = Select(
    title="Hazard Type",
    options=sorted(CURRENT_STATE.hazard_types),
    value=CURRENT_STATE.selected_hazard_type,
    width=200
)
select_hazard_type.on_change("value", on_hazard_type_changed)

select_source_sector = Select(
    title="Impacted Sector",
    options=sorted(CURRENT_STATE.impacted_sectors),
    value=CURRENT_STATE.selected_impacted_sector,
    width=200
)
select_source_sector.on_change("value", on_impacted_sector_changed)
select_source_sector.sizing_mode = "fixed"

select_metric = Select(
    title="Metric",
    options=sorted(CURRENT_STATE.metrics),
    value=CURRENT_STATE.selected_metric,
    width=200
)
select_metric.on_change("value", on_metric_changed)
select_metric.sizing_mode = "fixed"

select_scenario = Select(
    title="Scenario",
    options=sorted(CURRENT_STATE.scenarios),
    value=CURRENT_STATE.selected_scenario,
    width=200
)
select_scenario.on_change("value", on_scenario_changed)
select_scenario.sizing_mode = "fixed"

select_ref_year = Select(
    title="Year",
    options=sorted(CURRENT_STATE.ref_years),
    value=CURRENT_STATE.selected_ref_year,
    width=200
)
select_ref_year.on_change("value", on_ref_year_changed)
select_ref_year.sizing_mode = "fixed"

select_io_approach = Select(
    title="IO Approach",
    options=sorted(CURRENT_STATE.io_approaches),
    value=CURRENT_STATE.selected_io_approach,
    width=200
)
select_io_approach.on_change("value", on_io_approach_changed)
select_io_approach.sizing_mode = "fixed"

button = Button(label="Update Runs", button_type="success")
button.on_click(update_state)

# The DataSources
geo_source = None
country_table_source = None
source_barplot = None

# This initializes the data
CURRENT_STATE.load_data()

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

p_barpot = figure(
    y_range=source_barplot.data['sectors'][::-1], height=1300, width=1400,
    title=f"Expected total production impact for Switzerland", tools=["tap", "reset", "save"]
)

p_barpot.hbar(y="sectors", right="impact", height=0.9, fill_alpha=0.9, source=source_barplot)
# p_barpot.sizing_mode = "stretch_both"
# p_barpot.min_border_left = 200
# p_barpot.y_range.start = 0
# p_barpot.xaxis.major_label_orientation = np.pi / 4

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
select_hazard_type.sizing_mode = "stretch_width"

tab = Tabs(
    tabs=[TabPanel(child=data_table_sector, title="Sectors"), TabPanel(child=data_table_country, title="Countries")]
)

lt = layout(
    [
        [select_run, select_hazard_type, select_source_sector, select_metric, select_scenario, select_ref_year,
         select_io_approach,
         Div(sizing_mode="stretch_width"), button],
        # TODO Add the new buttons here  select_scenario, select_ref_year,select_io_approach
        [[p_countries, tab], [p_barpot]]
    ],
    sizing_mode="stretch_width"
)
curdoc().add_root(lt)
curdoc().title = "NCCS - Dashboard"
print("Done!\nTo show the Dashboard run:\nbokeh serve nccs\dashboard.py --show")
