import os
from utils import folder_naming
from shutil import rmtree

def delete_results_folder(run_title):
    run_dir = folder_naming.get_run_dir(run_title)
    if os.path.exists(run_dir):
        print(f'Removing results in {run_dir}')
        rmtree(run_dir)
    else:
        print(f'No results to remove in {run_dir}')
    