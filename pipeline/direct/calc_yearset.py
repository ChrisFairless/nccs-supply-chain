import random

import numpy as np
from climada.util import yearsets
from scipy import sparse


# PATCHING A BROKEN IMHO FUNCTION
def sample_from_poisson(n_sampled_years, lam, seed=None):
    """Sample the number of events for n_sampled_years

    Parameters
    -----------
        n_sampled_years : int
            The target number of years the impact yearset shall contain.
        lam: int
            the applied Poisson distribution is centered around lambda events per year
        seed : int, optional
            seed for numpy.random, will be set if not None
            default: None

    Returns
    -------
        events_per_year : np.ndarray
            Number of events per sampled year
    """
    if seed is not None:
        np.random.seed(seed)
    if lam != 1:
        events_per_year = np.round(
            np.random.poisson(
                lam=lam,
                size=n_sampled_years
            )
        ).astype('int')
    else:
        # events_per_year = np.ones(len(n_sampled_years)) # this is the original line
        events_per_year = np.ones(n_sampled_years).astype('int')

    return events_per_year


yearsets.sample_from_poisson = sample_from_poisson


def nccs_yearsets_simple(impact_list, n_sim_years, seed=1312):
    '''
    Generate yearsets from a list of impact objects.
    TODO: Make this more complex so that the year sampling is consistent across hazards
    i.e. when Cyclone X is selected in year Y for one yearset, it is selected in all cyclone yearsets
    '''
    random.seed(seed)
    return [yimp_from_imp_simple(imp, n_sim_years, seed=random.randint(1, 999999999)) for imp in impact_list]


def yimp_from_imp_simple(imp, n_sim_years, seed=1312):
    lam = np.sum(imp.frequency)
    yimp, samp_vec = yearsets.impact_yearset(
        imp,
        lam=lam,
        sampled_years=list(range(1, n_sim_years + 1)),
        correction_fac=False,
        seed=seed
    )
    yimp.imp_mat = sparse.csr_matrix(
        np.vstack(
            [imp.imp_mat[samp_vec[i]].sum(0)
             for i in range(len(samp_vec))
             ]
        )
    )
    return yimp
