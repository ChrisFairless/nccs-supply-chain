"""
This file contains the full run of the pipeline. Some combinations are currently commented out, because they are not
either not yet fully developed (windstorms) or has not yet been decided which combinations are relevant
"""

CONFIG = {
    "run_title": "test_run",
    "io_approach": "ghosh",
    "n_sim_years": 100,
    "runs": [
        {
            "hazard": "tropical_cyclone",
            "sectors": ["wood"],
            "countries": ['Germany', 'United States', 'Argentina', 'China', 'Cuba'],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"}

            ]
        },
        # {
        #     "hazard": "river_flood",
        #     "sectors": ["manufacturing", "mining"],
        #     "countries": ['United States','Fiji'],
        #     "scenario_years": [
        #         {"scenario": "None", "ref_year": "historical"},
        #     ]
        # },
    ]
}
