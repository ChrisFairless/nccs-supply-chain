from climada_petals.engine import SupplyChain

import numpy as np

from bokeh.plotting import figure, show, output_file
from bokeh.layouts import layout
from bokeh.models import ColumnDataSource
from bokeh.transform import linear_cmap


def plot_tot_prod_impt_eai(data):
    """Plot indirect impact"""
    data = [(k, v) for k, v in sorted(data.items())]
    data = sorted(data, key=lambda x: x[1], reverse=True)

    sectors = [k[0][:50] for k in data]
    values = [k[1] for k in data]

    source = ColumnDataSource(
        dict(
            sectors = sectors,
            impact = values
        )
    )
    p = figure(
        x_range=sectors, height=700, width=1400, title="Expected total production impact for Switzerland",
    )

    p.vbar(x="sectors", top="impact", width=0.9, source=source)

    p.y_range.start = 0
    p.xaxis.major_label_orientation = np.pi/4

    return p

def plot_source_matrix(data, x_range=None):

    #  Currently only one country
    data = [(k, v, "USA") for k, v in sorted(data.items())]
    data = sorted(data, key=lambda x: x[1], reverse=True)

    sectors = [k[0][:50] for k in data]
    values = [k[1] for k in data]
    countries = [k[2] for k in data]

    source = ColumnDataSource(
        dict(
            sectors = sectors,
            impact = values,
            country = countries
        )
    )

    cmap = linear_cmap(
        "impact", palette="Inferno256",
        low=min(values), high=max(values)
    )
    p = figure(
        x_range=x_range, y_range=list(set(countries)), height=100, width=1400, title="Expected total production impact for Switzerland",
    )
    p.circle(x='sectors', y='country', color=cmap, size=10, source=source, )
    p.xaxis.major_label_text_color = None
    return p



def create_supply_chain_vis(supchain: SupplyChain):
    """Create supply chain visualization"""
    output_file(filename="custom_filename.html", title="Static HTML file")

    data = supchain.tot_prod_impt_eai.loc[('CHE', slice(None))]
    p1 = plot_tot_prod_impt_eai(data)
    p2 = plot_source_matrix(data, x_range=p1.x_range)
    show(layout([p2, p1]))

