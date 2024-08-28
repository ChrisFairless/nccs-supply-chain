"""
This file contains config dictionaries for some small example analyses.
Each object contains one run with a different hazard and a few countries and can be imported seperately in your analysis.
"""

import pathos as pa
ncpus = 3
ncpus = pa.helpers.cpu_count() - 1


CONFIG = {
    "run_title": "test_run",
    "n_sim_years": 300,                 # Number of stochastic years of supply chain impacts to simulate
    "io_approach": ["ghosh"],           # Supply chain IO to use. One or more of "leontief", "ghosh".
    "seed": 161,

    # Which parts of the model chain to run:
    "do_direct": True,                  # Calculate direct impacts (that aren't already calculated)
    "do_yearsets": True,                # Calculate direct impact yearsets (that aren't already calculated)
    "do_multihazard": False,            # Also combine hazards to create multi-hazard supply chain shocks
    "do_indirect": True,                # Calculate any indirect supply chain impacts (that aren't already calculated)

    # Impact functions:
    "business_interruption": True,      # Turn off to assume % asset loss = % production loss. Mostly for debugging and reproducibility
    "calibrated": True,                 # Turn off to use best guesstimate impact functions. Mostly for debugging and reproducibility

    # Parallisation:
    "do_parallel": True,                # Parallelise some operations
    "ncpus": ncpus,

    "runs": [
        {
            "hazard": "tropical_cyclone",
            "sectors": ["manufacturing"],
            "countries": ['United States', 'Ireland', 'Japan', 'Taiwan, Province of China', 'China', 'Korea, Republic of'],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
            ]
        }
    ]
}

CONFIG2 = {
    "run_title": "test_run",
    "n_sim_years": 300,                 # Number of stochastic years of supply chain impacts to simulate
    "io_approach": ["ghosh"],           # Supply chain IO to use. One or more of "leontief", "ghosh".
    "seed": 161,

    # Which parts of the model chain to run:
    "do_direct": True,                  # Calculate direct impacts (that aren't already calculated)
    "do_yearsets": True,                # Calculate direct impact yearsets (that aren't already calculated)
    "do_multihazard": False,            # Also combine hazards to create multi-hazard supply chain shocks
    "do_indirect": True,                # Calculate any indirect supply chain impacts (that aren't already calculated)

    # Impact functions:
    "business_interruption": True,      # Turn off to assume % asset loss = % production loss. Mostly for debugging and reproducibility
    "calibrated": True,                 # Turn off to use best guesstimate impact functions. Mostly for debugging and reproducibility

    # Parallisation:
    "do_parallel": True,                # Parallelise some operations
    "ncpus": ncpus,

    "runs": [
        {
            "hazard": "river_flood",
            "sectors": ["manufacturing"],
            "countries": ['China','Germany','Burundi','Italy'],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
            ]
        }
    ]
}

CONFIG3 = {
    "run_title": "test_run",
    "n_sim_years": 300,                 # Number of stochastic years of supply chain impacts to simulate
    "io_approach": ["ghosh"],           # Supply chain IO to use. One or more of "leontief", "ghosh".
    "seed": 161,

    # Which parts of the model chain to run:
    "do_direct": True,                  # Calculate direct impacts (that aren't already calculated)
    "do_yearsets": True,                # Calculate direct impact yearsets (that aren't already calculated)
    "do_multihazard": False,            # Also combine hazards to create multi-hazard supply chain shocks
    "do_indirect": True,                # Calculate any indirect supply chain impacts (that aren't already calculated)

    # Impact functions:
    "business_interruption": True,      # Turn off to assume % asset loss = % production loss. Mostly for debugging and reproducibility
    "calibrated": True,                 # Turn off to use best guesstimate impact functions. Mostly for debugging and reproducibility

    # Parallisation:
    "do_parallel": True,                # Parallelise some operations
    "ncpus": ncpus,

    "runs": [
        {
            "hazard": "wildfire",
            "sectors": ["manufacturing"],
            "countries": ['Italy','China','Russian Federation'],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
            ]
        }
    ]
}

CONFIG4 = {
    "run_title": "test_run",
    "n_sim_years": 300,                 # Number of stochastic years of supply chain impacts to simulate
    "io_approach": ["ghosh"],           # Supply chain IO to use. One or more of "leontief", "ghosh".
    "seed": 161,

    # Which parts of the model chain to run:
    "do_direct": True,                  # Calculate direct impacts (that aren't already calculated)
    "do_yearsets": True,                # Calculate direct impact yearsets (that aren't already calculated)
    "do_multihazard": False,            # Also combine hazards to create multi-hazard supply chain shocks
    "do_indirect": True,                # Calculate any indirect supply chain impacts (that aren't already calculated)

    # Impact functions:
    "business_interruption": True,      # Turn off to assume % asset loss = % production loss. Mostly for debugging and reproducibility
    "calibrated": True,                 # Turn off to use best guesstimate impact functions. Mostly for debugging and reproducibility

    # Parallisation:
    "do_parallel": True,                # Parallelise some operations
    "ncpus": ncpus,

    "runs": [
        {
            "hazard": "storm_europe",
            "io_approach": ["ghosh"],
            "sectors": ["manufacturing"],
            "countries": ['Germany','Ireland'],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
            ]
        }
    ]
}

CONFIG5 = {
    "run_title": "test_run",
    "n_sim_years": 300,                         # Number of stochastic years of supply chain impacts to simulate
    "io_approach": ["leontief", "ghosh"],       # Supply chain IO to use. One or more of "leontief", "ghosh".
    "seed": 161,

    # Which parts of the model chain to run:
    "do_direct": True,                  # Calculate direct impacts (that aren't already calculated)
    "do_yearsets": True,                # Calculate direct impact yearsets (that aren't already calculated)
    "do_multihazard": False,            # Also combine hazards to create multi-hazard supply chain shocks
    "do_indirect": True,                # Calculate any indirect supply chain impacts (that aren't already calculated)

    # Impact functions:
    "business_interruption": True,      # Turn off to assume % asset loss = % production loss. Mostly for debugging and reproducibility
    "calibrated": True,                 # Turn off to use best guesstimate impact functions. Mostly for debugging and reproducibility

    # Parallisation:
    "do_parallel": True,                # Parallelise some operations
    "ncpus": ncpus,

    "runs": [
        {
            "hazard": "relative_crop_yield",
            "sectors": ["agriculture"],
            "countries": ['Canada','Egypt', 'Portugal','Pakistan','Armenia','Belarus','Peru'],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
                {"scenario": "rcp60", "ref_year": "future"},
            ]
        }
    ]
}
