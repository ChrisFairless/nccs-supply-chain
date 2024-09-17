"""
Test the analysis pipeline runs
"""

import unittest
from analysis import run_pipeline_from_config
from run_configurations.test.test_config import CONFIG  # change here to test_config if needed
from utils.folder_naming import get_direct_output_dir
from utils.delete_results import delete_results_folder

class TestAnalysisPipeline(unittest.TestCase):
    
    # Simplest possible test: check it runs without errors
    # TODO: less simple possible tests 
    def test_pipeline_runs(self):
        CONFIG = {
            "run_title": "unittest",
            "n_sim_years": 10,                  # Number of stochastic years of supply chain impacts to simulate
            "io_approach": ["ghosh"],           # Supply chain IO to use. One or more of "leontief", "ghosh"
            "force_recalculation": False,       # If an intermediate file or output already exists should it be recalculated?
            "use_s3": False,                    # Also load and save data from an S3 bucket
            "log_level": "INFO",
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
            "ncpus": 1,

            # Run specifications:
            "runs": [
                {
                    "hazard": "test",
                    "sectors": ["test"],
                    "countries": ["Dominica"],
                    "scenario_years": [
                        {"scenario": "test", "ref_year": "test"},
                    ]
                }
            ]
        }

        delete_results_folder(CONFIG['run_title'])
        _ = run_pipeline_from_config(CONFIG)


if __name__ == '__main__':
    unittest.main()
