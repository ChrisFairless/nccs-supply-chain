"""
This file contains the full run of the pipeline. Some combinations are currently commented out, because they are not
either not yet fully developed (windstorms) or has not yet been decided which combinations are relevant
"""

CONFIG = {
    "run_title": "test_run",
    "n_sim_years": 100,
    "io_approach_list": ["leontief", "ghosh"],
    "seed": 161,
    "runs": [
        {
            "hazard": "storm_europe",
            "sectors": ["agriculture","forestry","mining", "manufacturing","service","energy", "water", "waste", "basic_metals","pharmaceutical", "food", "wood", "chemical","rubber_and_plastic","non_metallic_mineral","refin_and_transform"],
            "countries": ['Germany'],
            "scenario_years": [
                {"scenario": "rcp26", "ref_year": "future"},
                {"scenario": "rcp85", "ref_year": "future"},

            ]
        },
        {
            "hazard": "relative_crop_yield",
            "sectors": ["agriculture"],
            "countries": ['United States','Fiji'],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
                {"scenario": "rcp60", "ref_year": "future"},
            ]
        },

        {
            "hazard": "wildfire",
            "sectors": ["agriculture","forestry","mining", "manufacturing","service","energy", "water", "waste", "basic_metals","pharmaceutical", "food", "wood", "chemical","rubber_and_plastic","non_metallic_mineral","refin_and_transform"],
            "countries": ['Afghanistan', "United States"],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
            ]
        },

        {
            "hazard": "river_flood",
            "sectors": ["agriculture","forestry","mining", "manufacturing","service","energy", "water", "waste", "basic_metals","pharmaceutical", "food", "wood", "chemical","rubber_and_plastic","non_metallic_mineral","refin_and_transform"],
            "countries": ["United States", "China"],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
                {"scenario": "rcp26", "ref_year": 2060},
                {"scenario": "rcp85", "ref_year": 2060},

            ]
        },

        {
            "hazard": "tropical_cyclone",
            "sectors": ["agriculture","forestry","mining", "manufacturing","service","energy", "water", "waste", "basic_metals","pharmaceutical", "food", "wood", "chemical","rubber_and_plastic","non_metallic_mineral","refin_and_transform"],
            "countries": ['Haiti', "China"],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
                {"scenario": "rcp26", "ref_year": "2060"},
                {"scenario": "rcp85", "ref_year": "2060"},
            ]
        },

    ]
}

