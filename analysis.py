from climada.util.api_client import Client
from climada_petals.engine import SupplyChain
from climada.entity import ImpfTropCyclone, ImpactFuncSet
from climada.engine.impact_calc import ImpactCalc

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






def main():
    client = Client()

    ### ------------------------------------ ###
    ### 1. CALCULATE DIRECT ECONOMIC IMPACTS ###
    ### ------------------------------------ ###

    exp_usa = client.get_litpop('USA')

    tc_usa = client.get_hazard('tropical_cyclone', properties={'country_iso3alpha':'USA', 'climate_scenario':'historical'})

    # Define direct_impact function
    impf_tc = ImpfTropCyclone.from_emanuel_usa()
    impf_set = ImpactFuncSet()
    impf_set.append(impf_tc)
    impf_set.check()

    # Calculate direct impacts to the USA due to TC
    imp_calc = ImpactCalc(exp_usa, impf_set, tc_usa)
    direct_impact_usa = imp_calc.impact()


    ### ----------------------------------- ###
    ### CALCULATE INDIRECT ECONOMIC IMPACTS ###
    ### ----------------------------------- ###

    supchain = SupplyChain.from_mriot(mriot_type='WIOD16', mriot_year=2011)

    # Assign exposure and stock direct_impact to MRIOT country-sector
    
    # (Service sector)
    impacted_secs = supchain.mriot.get_sectors()[range(26,56)].tolist()
    supchain.calc_secs_exp_imp_shock(exp_usa, direct_impact_usa, impacted_secs)

    # Calculate local production losses
    supchain.calc_direct_production_impacts(direct_impact_usa)

    # Calculate the propagation of production losses
    supchain.calc_indirect_production_impacts(direct_impact_usa, io_approach='ghosh')

    # Calculate total production loss
    supchain.calc_total_production_impacts(direct_impact_usa)

    # Some basic Vis
    create_supply_chain_vis(supchain)
    # Everything in this section equivalent to
    #    supchain.calc_production_impacts(direct_impact_usa, exp_usa, impacted_secs=impacted_secs, io_approach='ghosh')


if __name__ == "__main__":
    main()