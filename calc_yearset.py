import numpy as np
import random
from scipy import sparse
from climada.util import yearsets

def nccs_yearsets_simple(impact_list, n_sim_years, seed=1312):
    '''
    Generate yearsets from a list of impact objects.
    TODO: Make this more complex so that the year sampling is consistent across hazards
    i.e. when Cyclone X is selected in year Y for one yearset, it is selected in all cyclone yearsets
    '''
    random.seed(seed)
    return [yimp_from_imp_simple(imp, n_sim_years, seed=random.randint(1,999999999)) for imp in impact_list]


def yimp_from_imp_simple(imp,  n_sim_years, seed=1312):
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
    return yimp
        
