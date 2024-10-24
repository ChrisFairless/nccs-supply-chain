import os
from nccs.utils import folder_naming
from shutil import rmtree
import logging

LOGGER = logging.getLogger(__name__)

def delete_results_folder(run_title):
    run_dir = folder_naming.get_run_dir(run_title)
    if os.path.exists(run_dir):
        LOGGER.info(f'Removing results in {run_dir}')
        rmtree(run_dir)
    else:
        LOGGER.info(f'No results to remove in {run_dir}')
    