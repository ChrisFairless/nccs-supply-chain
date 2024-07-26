import os

OUTPUT_DIR = os.path.abspath(f"{os.path.dirname(__file__)}/../results")


def get_resource_dir():
    """
    Returns the absolute path to the exposures directory
    :return:
    """
    return os.path.abspath(f"{os.path.dirname(os.path.abspath(__file__))}/../resources")

def get_resources_dir():
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


def get_namestring_generic(prefix, extension, haz_type, sector, scenario, ref_year, country_iso3alpha):
    return f"{prefix}" \
           f"_{haz_type}" \
           f"_{sector.replace(' ', '_')[:15]}" \
           f"_{scenario}" \
           f"_{ref_year}" \
           f"_{country_iso3alpha}" \
           f".{extension}"


def get_namestring_direct(haz_type, sector, scenario, ref_year, country_iso3alpha):
    return get_namestring_generic(
        prefix="impact_raw",
        extension="hdf5",
        haz_type=haz_type,
        sector=sector,
        scenario=scenario,
        ref_year=ref_year,
        country_iso3alpha=country_iso3alpha
        )

def get_namestring_yearset(haz_type, sector, scenario, ref_year, country_iso3alpha):
    return get_namestring_generic(
        prefix='yearset',
        extension='hdf5',
        haz_type=haz_type,
        sector=sector,
        scenario=scenario,
        ref_year=ref_year,
        country_iso3alpha=country_iso3alpha
        )

def get_namestring_supchain_direct(haz_type, sector, scenario, ref_year, country_iso3alpha):
    return get_namestring_generic(
        prefix="direct_impacts",
        extension="csv",
        haz_type=haz_type,
        sector=sector,
        scenario=scenario,
        ref_year=ref_year,
        country_iso3alpha=country_iso3alpha
    )

def get_namestring_supchain_indirect(haz_type, sector, scenario, ref_year, io_approach, country_iso3alpha):
    return "indirect_impacts" \
           f"_{haz_type}" \
           f"_{sector.replace(' ', '_')[:15]}" \
           f"_{scenario}" \
           f"_{ref_year}" \
           f"_{io_approach}" \
           f"_{country_iso3alpha}" \
           f".csv"
