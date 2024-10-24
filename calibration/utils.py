import sys
sys.path.append('../..')
from pathlib import Path
import os
import numpy as np
import pandas as pd
from itertools import compress
from climada.engine import Impact
import pycountry
import logging

sys.path.append('../..')
from nccs.utils.folder_naming import get_resources_dir, get_direct_output_dir
from nccs.analysis import run_pipeline_from_config
from nccs.pipeline.direct.direct import HAZ_N_YEARS

LOGGER = logging.getLogger(__name__)


def write_sigmoid_impf_to_file(hazard_type, v_half, scale, v_thresh=25.8):
    impf_df = pd.DataFrame(dict(v_thresh=[v_thresh], v_half=[v_half], scale=[scale]))
    impf_path = Path(get_resources_dir(), 'impact_functions', hazard_type, 'custom.csv')
    impf_df.to_csv(impf_path, index=False)


def write_scaled_impf_to_file(hazard_type, impf, translate = 0, scale = 1):
    if np.any(scale * impf.mdd > 1):
        raise ValueError(f'The chosen scaling of {scale} takes MDD above 100%. TODO: code around this')
    scaled_impf = ImpactFunc(
        name = "Scaled " + impf.name,
        id = 1,
        intensity_unit = impf.intensity_unit,
        intensity = impf.intensity + translate,
        paa = impf.paa,
        mdd = scale * mdd
    )
    scaled_impf.check()
    df = pd.DataFrame(dict(
        id = scaled_impf.id,
        intensity = scaled_impf.intensity,
        paa = scaled_impf.paa,
        mdd = scaled_impf.mdd
    ))
    output_path = Path(get_resources_dir(), 'impact_functions', hazard_type, 'custom.csv')
    df.to_csv(output_path)


def return_period_impacts_from_config(config):
    # Run the pipeline
    analysis_df = run_pipeline_from_config(config)

    # Load results to match the observations
    countries = config['runs'][0]['countries']
    direct_output_dir = get_direct_output_dir(config['run_title'])
    raw_impact_filenames = {country: list(analysis_df[analysis_df['country']==country]['direct_impact_path'])[0] for country in countries}
    imp_path_country = {country: Path(direct_output_dir, raw_impact_filenames[country]) for country in countries}
    imp_exists = np.array([os.path.exists(imp_path_country[country]) for country in countries])
    countries_missing = list(compress(countries, ~imp_exists))
    countries = list(compress(countries, imp_exists))
    if len(countries_missing) > 0:
        LOGGER.warning(f'No output data found for countries {countries_missing}')

    imp_country = [
        pd.DataFrame({
            'country': pycountry.countries.get(name=country).alpha_3,
            'impact': Impact.from_hdf5(imp_path_country[country]).at_event
            })
        for country in countries
        ]
    
    for imp in imp_country:
        if not np.any([imp['impact']]):
            LOGGER.warning(f'No modelled impacts in country {imp["country"][0]}')

    if len(imp_country) == 0:
        raise ValueError('No impacts found')

    df = pd.concat(imp_country)
    df = df.sort_values(['country', 'impact'], ascending=[True, False])
    df['rank'] = df.groupby(['country']).cumcount() + 1

    assert(len(config['runs']) == 1)
    n_years = HAZ_N_YEARS[config['runs'][0]['hazard']]
    df['rp'] = df.groupby(['country'])['rank'].transform(lambda x: n_years / x) 
    df = df[['country', 'impact', 'rp']]
    df = df.reset_index()
    
    df = df[df['rp'] >= 1]  # save a huge amount of memory by not saving events with very low return periods. Note: this makes the dataset unsuitable for an average annual loss calculation
    
    return df