import glob
import logging
import os
from logging import ERROR, getLogger

import numpy as np
import pandas as pd

from nccs.analysis import run_pipeline_from_config
from multiprocessing import Pool
getLogger('nccs.analysis').setLevel(ERROR)


def calc_error(file_no_bi, file_bi, weight: float) -> [float, float, float]:
    df = pd.read_csv(file_no_bi)
    sum_aapl_no_bi = df['AAPL'].sum()

    df = pd.read_csv(file_bi)
    sum_aapl_bi = df['AAPL'].sum()

    return abs(sum_aapl_no_bi * weight - sum_aapl_bi), sum_aapl_no_bi, sum_aapl_bi


def optimize(country, hazard, sectors, n_iterations=20, initial_scale=1, weight=0.47):
    lst_cost = np.inf
    for i in range(n_iterations):
        print(f"Iteration:{i}, Current scale:{initial_scale}")
        os.environ['BI_CALIBRATION_SCALE'] = str(round(initial_scale, 6))
        # Run the pipeline
        config['run_title'] = f'bi-calibration-bi-{country}-{hazard}-{i}'
        config['business_interruption'] = True
        config['runs'][0]['sectors'] = sectors
        config['runs'][0]['hazard'] = hazard
        config['runs'][0]['countries'] = [country]
        run_pipeline_from_config(config)
        file_bi = glob.glob(f'results/{config["run_title"]}/direct/*{sectors[0]}*.csv')[0]

        config['run_title'] = f'bi-calibration-no-bi-{country}-{hazard}-{i}'
        config['business_interruption'] = False
        config['runs'][0]['sectors'] = sectors
        config['runs'][0]['hazard'] = hazard
        config['runs'][0]['countries'] = [country]
        run_pipeline_from_config(config)
        file_no_bi = glob.glob(f'results/{config["run_title"]}/direct/*{sectors[0]}*.csv')[0]

        cost, no_bi, bi = calc_error(file_no_bi, file_bi, weight)
        print(f'Cost: {cost}, no_bi: {no_bi}, bi: {bi}')
        if cost < lst_cost:
            lst_cost = cost
            initial_scale = initial_scale - 0.05
            os.remove(file_bi)
            os.remove(file_no_bi)
        else:
            print(f'Cost: {cost}, final scale: {initial_scale}')
            return {"cost": cost, "no_bi": no_bi, "bi": bi, "scale": initial_scale}


if __name__ == '__main__':
    # Configuration to calibrate against
    config = {
        "run_title": "bi-calibration-tc",
        "n_sim_years": 300,  # Number of stochastic years of supply chain impacts to simulate
        "io_approach": ["leontief", "ghosh"],  # Supply chain IO to use. One or more of "leontief", "ghosh"
        "force_recalculation": False,  # If an intermediate file or output already exists should it be recalculated?
        "use_s3": False,  # Also load and save data from an S3 bucket
        "log_level": "INFO",
        "seed": 161,

        # Which parts of the model chain to run:
        "do_direct": True,  # Calculate direct impacts (that aren't already calculated)
        "do_yearsets": True,  # Calculate direct impact yearsets (that aren't already calculated)
        "do_multihazard": False,  # Also combine hazards to create multi-hazard supply chain shocks
        "do_indirect": True,  # Calculate any indirect supply chain impacts (that aren't already calculated)

        # Impact functions:
        "business_interruption": True,
        # Turn off to assume % asset loss = % production loss. Mostly for debugging and reproducibility
        "calibrated": True,
        # Turn off to use best guesstimate impact functions. Mostly for debugging and reproducibility

        # Parallisation:
        "do_parallel": False,  # Parallelise some operations
        "ncpus": 6,

        "runs": [
            {
                "hazard": "river_flood",
                "sectors": [
                    # "agriculture",
                    # "forestry", "mining",
                    "manufacturing",
                    # "service", "energy", "water",
                    # "waste"
                ],
                "countries": ['United States'],
                "scenario_years": [
                    {"scenario": "None", "ref_year": "historical"},
                    # {"scenario": "rcp26", "ref_year": "2060"},
                ]
            }
        ]
    }

#Option 1: all countries
    # file_path = r"C:\Users\AlinaMastai\Correntics\Correntics - Documents\Collaborations\NCCS\2024-04_BI_Impact_functions\2024-10-BI-calibration\bi_scaling.xlsx"
    # df = pd.read_excel(file_path)
    # countries = list(zip(df['Countries'], df['bi_scale']))

#Option 2: Reduced country set
    countries = [
        ("United States", 0.31),
        ("Germany", 0.41),
        ("China", 0.29),
        ("Nigeria", 0.36),
        ("Japan", 0.29)
    ]

    result = []
    for country, weight in countries:
        for sector in ["forestry", "mining", "manufacturing", "service", "energy"]:
            try:
                res = optimize(country, "river_flood", [sector], 20, 0.9, weight)
                res['country'] = country
                res['sector'] = sector
                res['hazard'] = 'river_flood'
                result.append(res)
            except Exception as e:
                logging.exception(e)
    pd.DataFrame(result).to_csv('results/bi-calibration-results_test_without.csv')


