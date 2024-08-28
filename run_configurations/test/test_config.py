"""
This file contains a very very simple run to check that the model pipeline can be run.
It doesn't look at the whole pipeline functionality!
"""

import pathos as pa
ncpus = 3
ncpus = pa.helpers.cpu_count() - 1

CONFIG = {
    "run_title": "unittest",
    "n_sim_years": 10,                  # Number of stochastic years of supply chain impacts to simulate
    "io_approach": ["ghosh"],           # Supply chain IO to use. One or more of "leontief", "ghosh"
    "force_recalculation": False,       # If an intermediate file or output already exists should it be recalculated?
    "use_s3": False,                    # Also load and save data from an S3 bucket
    "seed": 42,

    # Which parts of the model chain to run:
    "do_direct": True,                  # Calculate direct impacts (that aren't already calculated)
    "do_yearsets": True,                # Calculate direct impact yearsets (that aren't already calculated)
    "do_multihazard": False,            # Also combine hazards to create multi-hazard supply chain shocks
    "do_indirect": True,                # Calculate any indirect supply chain impacts (that aren't already calculated)

    # Impact functions:
    "business_interruption": True,      # Turn off to assume % asset loss = % production loss. Mostly for debugging and reproducibility
    "calibrated": True,                 # Turn off to use best guesstimate impact functions. Mostly for debugging and reproducibility

    # Parallisation:
    "do_parallel": False,                # Parallelise some operations
    "ncpus": ncpus,

    # Run specifications:
    "runs": [
        {
            "hazard": "tropical_cyclone",
            "sectors": ["service", "agriculture"],
            "countries": ["Dominica"],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
            ]
        },
        {
            "hazard": "storm_europe",
            "sectors": ["mining", "forestry"],
            "countries": ["Andorra"],
            "scenario_years": [
                {"scenario": "rcp85", "ref_year": "future"},
            ]
        }
    ]
}