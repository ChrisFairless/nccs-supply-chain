"""
This script is used to sync the files in the run directory to the S3 bucket.
How to use:

# mode is either "upload" or "download"

template:
python sync_s3.py --run_title <run_title> --mode <mode>

example:
python sync_s3.py --run_title test_run --mode upload

"""

import argparse
import glob
import os

from utils.folder_naming import get_run_dir
from utils.s3client import upload_to_s3_bucket

parser = argparse.ArgumentParser()
parser.add_argument("--run_title", type=str, required=True)
parser.add_argument("--mode", type=str, required=True, choices=["upload", "download"])


def upload_files(run_title):
    root_path = get_run_dir(run_title)
    files_to_sync = glob.glob(f"{root_path}/**/*", recursive=True)

    for f in files_to_sync:
        if os.path.isdir(f):
            continue
        bucket_file = os.path.relpath(f, os.path.dirname(__file__)).replace("\\", "/")
        upload_to_s3_bucket(f, bucket_file)


if __name__ == '__main__':

    args = parser.parse_args()
    run_title = args.run_title
    mode = args.mode

    assert mode in ["upload", "download"], "mode must be either 'upload' or 'download'"

    if mode == "upload":
        upload_files(run_title)
    else:
        # TODO
        raise NotImplementedError("download not implemented yet")
