"""
Test the analysis pipeline runs
"""

import unittest
from analysis import run_pipeline_from_config
from run_configurations.test.test_config import CONFIG  # change here to test_config if needed

class TestAnalysisPipeline(unittest.TestCase):
    
    # Simplest possible test: check it runs without errors
    # TODO: less simple possible tests 
    def test_pipeline_runs(self):
        _ = run_pipeline_from_config(CONFIG)


if __name__ == '__main__':
    unittest.main()
