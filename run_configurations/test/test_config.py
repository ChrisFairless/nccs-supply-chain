"""
This file contains a very very simple run to check that the model pipeline can be run.
It doesn't look at the whole pipeline functionality!
"""

CONFIG = {
    "run_title": "testing",
    "n_sim_years": 10,
    "runs": [
        {
            "hazard": "tropical_cyclone",
            "io_approach": ["ghosh"],
            "sectors": ["service", "agriculture"],
            "countries": ["Dominica"],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
            ]
        },
        {
            "hazard": "storm_europe",
            "io_approach": ["leontief"],
            "sectors": ["mining", "forestry"],
            "countries": ["Andorra"],
            "scenario_years": [
                {"scenario": "rcp85", "ref_year": "future"},
            ]
        }
    ]
}