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
        delete_results_folder(CONFIG['run_title'])
        _ = run_pipeline_from_config(CONFIG)


if __name__ == '__main__':
    unittest.main()
