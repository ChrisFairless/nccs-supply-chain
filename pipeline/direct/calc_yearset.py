import numpy as np
from climada.util import yearsets
from scipy import sparse


# THIS IS A QUICK FIX FOR A MORE COMPLEX PROBLEM
# CLIMADA's yearsets currently generate years of data through a Poisson process. That is, the number of 'events' in a 
# year is a random variable. This is great when our events are e.g. tropical cyclones and we're sampling from a 
# stochastic set. It doesn't work when our events are e.g. wildfire or windstorm years. In this case we always want to 
# sample exactly one 'event' per year. At some point we can add this functionality to CLIMADA as an additional method
# within the yearsets code, but for now I'm making a workaround where if the Poisson process is asked to sample events 
# with a frequency of 1/year it doesn't implement a Poisson process and instead returns exactly one event per year.
# This isn't a valid fix because it's plausible that a user would eventually ask for a Poisson process with lamda = 1/yr 
# and wouldn't be able to get that.
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
        events_per_year = np.ones(n_sampled_years).astype('int')

    return events_per_year


yearsets.sample_from_poisson = sample_from_poisson


def nccs_yearsets_simple(impact_list, n_sim_years, seed=None):
    '''
    Generate yearsets from a list of impact objects.
    TODO: Make this more complex so that the year sampling is consistent across hazards
    i.e. when Cyclone X is selected in year Y for one yearset, it is selected in all cyclone yearsets
    '''
    return [yimp_from_imp_simple(imp, n_sim_years, seed=seed) for imp in impact_list]


def yimp_from_imp_simple(imp, n_sim_years, seed=None):
    if np.all(imp.frequency == 1):
        lam = 1 
    else:
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
