"""
This file contains the full run of the pipeline. Some combinations are currently commented out, because they are not
either not yet fully developed (windstorms) or has not yet been decided which combinations are relevant
"""

CONFIG = {
    "run_title": "test_run",
    "n_sim_years": 300,
    "apply_business_interruption": False,    # Turn off to assume % asset loss = % production loss. Mostly for debugging and reproducing old results
    "use_calibrated_impfs": False,           # Turn off to use best guesstimate impact functions. Mostly for debugging and reproducing old results
    "runs": [
        {
            "hazard": "tropical_cyclone",
            "io_approach": ["ghosh"],
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
    "n_sim_years": 300,
    "apply_business_interruption": True,    # Turn off to assume % asset loss = % production loss. Mostly for debugging and reproducing old results
    "use_calibrated_impfs": True,           # Turn off to use best guesstimate impact functions. Mostly for debugging and reproducing old results
    "runs": [
        {
            "hazard": "river_flood",
            "io_approach": ["ghosh"],
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
    "n_sim_years": 300,
    "apply_business_interruption": True,    # Turn off to assume % asset loss = % production loss. Mostly for debugging and reproducing old results
    "use_calibrated_impfs": True,           # Turn off to use best guesstimate impact functions. Mostly for debugging and reproducing old results
    "runs": [
        {
            "hazard": "wildfire",
            "io_approach": ["ghosh"],
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
    "n_sim_years": 300,
    "apply_business_interruption": True,    # Turn off to assume % asset loss = % production loss. Mostly for debugging and reproducing old results
    "use_calibrated_impfs": True,           # Turn off to use best guesstimate impact functions. Mostly for debugging and reproducing old results
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
    "n_sim_years": 300,
    "apply_business_interruption": True,    # Turn off to assume % asset loss = % production loss. Mostly for debugging and reproducing old results
    "use_calibrated_impfs": True,           # Turn off to use best guesstimate impact functions. Mostly for debugging and reproducing old results
    "runs": [
        {
            "hazard": "relative_crop_yield",
            "io_approach": ["ghosh", "leontief"],
            "sectors": ["agriculture"],
            "countries": ['Canada','Egypt', 'Portugal','Pakistan','Armenia','Belarus','Peru'],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
                {"scenario": "rcp60", "ref_year": "future"},
            ]
        }
    ]
}
