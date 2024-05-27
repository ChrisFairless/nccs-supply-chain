"""
This file contains the full run of the pipeline. Some combinations are currently commented out, because they are not
either not yet fully developed (windstorms) or has not yet been decided which combinations are relevant
"""

CONFIG = {
    "run_title": "debugging",
    "n_sim_years": 100,
    "runs": [
        {
            "hazard": "wildfire",
            "io_approach": ["leontief", "ghosh"],
            "sectors": ["manufacturing"],
            "countries": ['Italy'],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
            ]
        }
    ]
}

