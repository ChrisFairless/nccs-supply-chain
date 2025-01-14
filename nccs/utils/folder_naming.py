import os

OUTPUT_DIR = os.path.abspath(f"{os.path.dirname(__file__)}/../../results")


def get_resource_dir():
    """
    Returns the absolute path to the exposures directory
    :return:
    """
    return os.path.abspath(f"{os.path.dirname(os.path.abspath(__file__))}/../../resources")

def get_resources_dir():
    """
    Returns the absolute path to the resources directory
    :return:
    """
    return os.path.abspath(f"{os.path.dirname(os.path.abspath(__file__))}/../../resources")


def get_output_dir():
    return OUTPUT_DIR


def get_run_dir(run_title):
    return f"{OUTPUT_DIR}/{run_title}"


def get_direct_output_dir(run_title):
    return f"{OUTPUT_DIR}/{run_title}/direct"


def get_indirect_output_dir(run_title):
    return f"{OUTPUT_DIR}/{run_title}/indirect"


def get_filename_generic(prefix, extension, hazard, sector, scenario, ref_year, country):
    return f"{prefix}" \
           f"_{hazard}" \
           f"_{sector.replace(' ', '_')[:15]}" \
           f"_{scenario}" \
           f"_{ref_year}" \
           f"_{country}" \
           f".{extension}"


def get_filename_direct(d: dict):
    return get_filename_generic(
        prefix="impact_raw",
        extension="hdf5",
        hazard=d['hazard'],
        sector=d['sector'],
        scenario=d['scenario'],
        ref_year=d['ref_year'],
        country=d['country']
        )

def get_filename_yearset(d: dict):
    return get_filename_generic(
        prefix='yearset',
        extension='hdf5',
        hazard=d['hazard'],
        sector=d['sector'],
        scenario=d['scenario'],
        ref_year=d['ref_year'],
        country=d['country']
        )

def get_filename_supchain_direct(d: dict):
    return get_filename_generic(
        prefix="direct_impacts",
        extension="csv",
        hazard=d['hazard'],
        sector=d['sector'],
        scenario=d['scenario'],
        ref_year=d['ref_year'],
        country=d['country']
    )

def get_filename_supchain_indirect(d: dict, io_approach: str):
    return "indirect_impacts" \
           f"_{d['hazard']}" \
           f"_{d['sector'].replace(' ', '_')[:15]}" \
           f"_{d['scenario']}" \
           f"_{d['ref_year']}" \
           f"_{io_approach}" \
           f"_{d['country']}" \
           f".csv"
