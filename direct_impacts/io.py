import os
import tempfile
import pycountry
from pathlib import Path
from climada.util.constants import DEF_CRS
from climada.engine import Impact

from utils.s3client import upload_to_s3_bucket, download_from_s3_bucket


def save_impact(imp, file_name, save_intermediate_dir, save_intermediate_s3, overwrite=False):
    with tempfile.NamedTemporaryFile() as f:   # We actually only use this when we're not saving locally
        if save_intermediate_dir:
            file_path = Path(save_intermediate_dir, file_name)
            if not overwrite and os.path.exists(file_path):
                raise FileExistsError(f'File already exists at {file_path}. Choose a different job_name or set overwrite=True')
        else:
            file_path = f.name
        imp.crs = DEF_CRS  # Until climada_python Issue #706 is solved
        imp.write_hdf5(file_path)
        if save_intermediate_s3:
            upload_to_s3_bucket(file_path, file_name)
        if not save_intermediate_dir:
            os.remove(file_path)


def load_impact(file_name, save_intermediate_dir, save_intermediate_s3):
    if save_intermediate_dir:
        file_path = Path(save_intermediate_dir, file_name)
        if os.path.exists(file_path):
            return Impact.from_hdf5(file_path)
    if save_intermediate_s3:
        with tempfile.NamedTemporaryFile() as f:
            download_from_s3_bucket(file_name, f.name)
            return Impact.from_hdf5(f.name)
    raise ValueError('Please set either save_intermediate_dir or save_intermediate_s3')


def get_job_filename(job_name, product, hazard, scenario, ref_year, sector, country):
    file_name = '_'.join([job_name, product, hazard.replace('_', ''), sector, scenario, str(ref_year), standardise_country(country)]) + '.hdf5'
    return file_name


def standardise_country(country):
    if len(country) == 3:
        return pycountry.countries.get(alpha_3=country).alpha_3
    else:
        return pycountry.countries.get(name=country).alpha_3