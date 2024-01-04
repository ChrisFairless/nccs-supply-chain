import os

OUTPUT_DIR = "./results"


def get_resource_dir():
    """
    Returns the absolute path to the resources directory
    :return:
    """
    return os.path.abspath(f"{os.path.dirname(os.path.abspath(__file__))}/../resources")


def get_output_dir():
    return OUTPUT_DIR


def get_run_dir(run_title):
    return f"{OUTPUT_DIR}/{run_title}"


def get_direct_output_dir(run_title):
    return f"{OUTPUT_DIR}/{run_title}/direct"


def get_indirect_output_dir(run_title):
    return f"{OUTPUT_DIR}/{run_title}/indirect"
