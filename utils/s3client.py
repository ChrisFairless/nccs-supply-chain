import os
import typing

import boto3
import dotenv

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


def download_from_s3_bucket(s3_filename: str, output_path: typing.Union[str, None] = None):
    """
    Downloads a file from the S3 bucket.
    if no output_path is provided, the file is downloaded to the current working directory.

    :param s3_filename:
    :param output_path:
    :return:
    """
    if output_path is None:
        output_path = s3_filename

    s3 = get_client()
    return s3.download_file(
        BUCKET_NAME,
        s3_filename,
        output_path
    )


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

    return s3.upload_file(
        input_filepath,
        BUCKET_NAME,
        s3_filename
    )


if __name__ == '__main__':
    with open("test.txt", "w") as f:
        f.write("test")

    upload_to_s3_bucket(input_filepath="test.txt", s3_filename="my-data-asset")
    download_from_s3_bucket(s3_filename="my-data-asset", output_path="test2.txt")

    os.remove("test.txt")
    os.remove("test2.txt")