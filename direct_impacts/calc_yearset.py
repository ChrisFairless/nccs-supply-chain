import numpy as np
import random
import datetime
from scipy import sparse
from climada.util import yearsets

from direct_impacts.io import save_impact, load_impact, get_job_filename

def nccs_yearsets_simple(
        analysis_df, 
        n_sim_years,
        save_intermediate_dir,
        save_intermediate_s3,
        load_saved_objects,
        overwrite,
        return_impact_objects,
        seed=1312):
    '''
    Generate yearsets from a list of impact objects.
    TODO: Make this more complex so that the year sampling is consistent across hazards
    i.e. when Cyclone X is selected in year Y for one yearset, it is selected in all cyclone yearsets
    '''
    if n_sim_years > datetime.MAXYEAR:
        raise ValueError(f'The number of simulated years is limited by the datetime module to {datetime.MAXYEAR}')
    random.seed(seed)
    analysis_df['file_name_yearset'] = [f.replace('_eventset_', '_yearset_') for f in analysis_df['file_name_eventset']]
    if load_saved_objects:
        if return_impact_objects:
            analysis_df['impact_yearset'] = [
                load_impact(
                    file_name=file_name,
                    save_intermediate_dir=save_intermediate_dir,
                    save_intermediate_s3=save_intermediate_s3
                    )
                for file_name in analysis_df['file_name_yearset']
            ]
        else:
            analysis_df['impact_yearset'] = [None for _ in analysis_df['file_name_yearset']]
        return analysis_df

    if return_impact_objects:
        imp_eventset_list = analysis_df['impact_eventset']
    else:
        imp_eventset_list = [
                load_impact(
                    file_name=file_name,
                    save_intermediate_dir=save_intermediate_dir,
                    save_intermediate_s3=save_intermediate_s3
                    )
                for file_name in analysis_df['file_name_eventset']
            ]
        
    yimp_list = [
        yimp_from_imp_simple(
            imp=imp,
            n_sim_years=n_sim_years,
            seed=random.randint(1,999999999),
            )
        for imp in imp_eventset_list
        ]
    if save_intermediate_dir or save_intermediate_s3:
        for yimp, file_name in zip(yimp_list, analysis_df['file_name_yearset']):
            save_impact(
                imp=yimp,
                file_name=file_name,
                save_intermediate_dir=save_intermediate_dir,
                save_intermediate_s3=save_intermediate_s3,
                overwrite=overwrite
                )
    analysis_df['impact_yearset'] = yimp_list if return_impact_objects else [None for _ in yimp_list]
    return analysis_df


def yimp_from_imp_simple(
        imp,
        n_sim_years,
        seed=1312
        ):
    lam = np.sum(imp.frequency)
    yimp, samp_vec = yearsets.impact_yearset(
        imp,
        lam=lam,
        sampled_years=list(range(1,n_sim_years+1)),
        correction_fac=False,
        seed=seed
        )
    yimp.imp_mat = sparse.csr_matrix(
        np.vstack([imp.imp_mat[samp_vec[i]].sum(0) 
                   for i in range(len(samp_vec))
                   ]))
    yimp.event_name = [f'year_{i}' for i in yimp.event_id]
    return yimp
        
