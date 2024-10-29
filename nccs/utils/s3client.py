import logging
import os
import typing
from pathlib import Path
import boto3
import dotenv
import botocore

from botocore.errorfactory import ClientError

from nccs.utils.folder_naming import get_output_dir

BUCKET_NAME = "nccs-modeling"


def get_client():
    """
    Returns a boto3 client for the S3 bucket. Make sure to set the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.
    :return:
    """
    dotenv.load_dotenv()
    access_key_id = os.environ.get("S3_ACCESS_KEY_ID")
    access_key = os.environ.get("S3_ACCESS_KEY")

    assert all(
        [access_key_id, access_key]
    ), "S3 credentials not set. Make sure S3_ACCESS_KEY_ID and S3_ACCESS_KEY are set in your environment or the .env " \
       "file."

    return boto3.client(
        "s3",
        aws_access_key_id=access_key_id,
        aws_secret_access_key=access_key
    )


def download_from_s3_bucket(s3_filename: str, output_path: typing.Union[str, None] = None, overwrite=False):
    """
    Downloads a file from the S3 bucket.
    if no output_path is provided, the file is downloaded to the current working directory.

    :param s3_filename:
    :param output_path:
    :return:
    """
    if output_path is None:
        output_path = s3_filename

    if not overwrite and os.path.exists(output_path):
        return

    dirname = os.path.dirname(output_path)
    if dirname != '':
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

    s3 = get_client()
    s3.download_file(
        BUCKET_NAME,
        s3_filename,
        output_path
    )


def download_folder_from_s3_bucket(s3_path: str, output_path: typing.Union[str, None] = None, overwrite=False):
    """
    Downloads a folder from the S3 bucket.
    if no output_path is provided, the file is downloaded to the current working directory.

    :param s3_path:
    :param output_path:
    :return:
    """
    if output_path is None:
        output_path = ''

    if not overwrite and os.path.exists(output_path):
        return

    dotenv.load_dotenv()
    access_key_id = os.environ.get("S3_ACCESS_KEY_ID")
    access_key = os.environ.get("S3_ACCESS_KEY")
    s3 = boto3.resource('s3', aws_access_key_id=access_key_id, aws_secret_access_key=access_key)

    bucket = s3.Bucket(BUCKET_NAME)
    for obj in bucket.objects.filter(Prefix=s3_path):
        if output_path=='':
            target = obj.key
        else:
            target = os.path.join(output_path, os.path.relpath(obj.key, s3_path))
        if not os.path.exists(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target))
        if obj.key[-1] == '/':
            continue
        print(target)
        bucket.download_file(obj.key, target)


def upload_to_s3_bucket(input_filepath: str, s3_filename: typing.Union[str, None] = None):
    """
    Uploads a file to the S3 bucket.
    if no s3_filename is provided, the filename of the input file is used.

    :param input_filepath: filepath of the file to upload
    :param s3_filename: key of the file in the S3 bucket
    :return:
    """
    if s3_filename is None:
        s3_filename = os.path.basename(input_filepath)

    s3 = get_client()
    s3.upload_file(
        input_filepath,
        BUCKET_NAME,
        s3_filename
    )

def file_exists_on_s3_bucket(s3_filename: str):
    s3 = get_client()
    try:
        s3.head_object(BUCKET_NAME, s3_filename)
        return True
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            # The key does not exist.
            return False
        elif e.response['Error']['Code'] == 403:
            # Unauthorized, including invalid bucket
            raise ClientError(e)
        else:
            raise ClientError(f"Unexpected error in the S3 client: {e}")


def download_complete_csvs_to_results():
    """
    Downloads all indirect/complete.csv files from the S3 bucket.
    :return:
    """
    logging.info("Downloading all indirect/complete.csv files from the S3 bucket.")
    client = get_client()
    paginator = client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix="results/"):
        for obj in page.get("Contents", []):
            filename = obj["Key"]
            logging.info(f"Scanning: {filename}")
            if filename.endswith("indirect/complete.csv"):
                if os.path.exists(filename):
                    logging.info(f"Skipping {filename} as it already exists.")
                    continue
                os.makedirs(os.path.dirname(filename), exist_ok=True)

                outfile = os.path.join(get_output_dir(), filename.replace("results/", ""))
                logging.info(f"Downloading {filename} to {outfile}")
                download_from_s3_bucket(filename, outfile)


# Upload results all the contents of a folder to S3
def upload_project_folder_to_s3(path_within_project: typing.Union[str, Path], s3_path: typing.Union[str, Path] = None) -> None:
    """
    Uploads a folder and its contents to the S3 bucket.
    if no s3_path is provided, the relative path of the input file in the project is used.

    :param path_within_project: filepath of the file to upload
    :param s3_filename: key of the file in the S3 bucket
    :return:
    """
    if not s3_path:
        s3_path = path_within_project
    repo_dir = Path(get_output_dir()).parent
    folder_path = Path(repo_dir, path_within_project)
    upload_folder_to_s3(path=folder_path, s3_path=s3_path)


def upload_folder_to_s3(path: typing.Union[str, Path], s3_path: typing.Union[str, Path]) -> None:
    for root, dirs, files in os.walk(path):
        files = [f for f in files if not f[0] == '.']
        dirs[:] = [d for d in dirs if not d[0] == '.']
        for f in files:
            local = Path(root, f)
            remote = Path(s3_path, local.relative_to(path))
            print(local)
            upload_to_s3_bucket(str(local), str(remote))




if __name__ == '__main__':
    print("Hello")
    with open("test.txt", "w") as f:
        f.write("test")

    upload_to_s3_bucket(input_filepath="test.txt", s3_filename="my-data-asset")
    download_from_s3_bucket(s3_filename="my-data-asset", output_path="test2.txt")

    os.remove("test.txt")
    os.remove("test2.txt")
