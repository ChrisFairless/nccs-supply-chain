"""
This file contains the full run of the pipeline. Some combinations are currently commented out, because they are not
either not yet fully developed (windstorms) or has not yet been decided which combinations are relevant
"""

CONFIG = {
    "run_title": "debugging",
    "n_sim_years": 100,
    "runs": [
        {
            "hazard": "river_flood",
            "io_approach": ["leontief", "ghosh"],
            "sectors": ["manufacturing"],
            "countries": ["Burundi"],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
                # {"scenario": "rcp26", "ref_year": 2020},
                # {"scenario": "rcp26", "ref_year": 2040},
                {"scenario": "rcp26", "ref_year": 2060},
                # {"scenario": "rcp26", "ref_year": 2080},
                # {"scenario": "rcp60", "ref_year": 2020},
                # {"scenario": "rcp60", "ref_year": 2040},
                # {"scenario": "rcp60", "ref_year": 2060},
                # {"scenario": "rcp60", "ref_year": 2080},
                # {"scenario": "rcp85", "ref_year": 2020},
                # {"scenario": "rcp85", "ref_year": 2040},
                {"scenario": "rcp85", "ref_year": 2060},
                # {"scenario": "rcp85", "ref_year": 2080},
            ]
        },
    ]
}

