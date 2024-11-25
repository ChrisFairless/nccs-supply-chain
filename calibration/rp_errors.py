import numpy as np
import pandas as pd
import logging
from copy import deepcopy
from sklearn.metrics import root_mean_squared_error

from calibration.interpolate_return_periods import interpolate_return_periods

LOGGER = logging.getLogger(__name__)

# Cost function to quantify the difference between modelled and observed model return periods

def rp_rmse(rp_model, rp_obs, grouping_var='country'):
    #Align return periods so that modelled data matches observations
    rp = merge_outputs_and_obs(rp_model, rp_obs, grouping_var)

    # DECISION: we use the root mean square error to evaluate model performance (not the log). This means that errors
    # from small events aren't very important and errors from large events dominate the cost function. This is what 
    # we want. (Other options to consider: root_mean_squared_log_error, mean_squared_error)

    # DECISION: all return periods are weighted equally. If we want to weight towards more extreme events we can 
    # reconsider this

    # DECISION: all events are weighted equally. That means that countries with more events have a stronger effect on 
    # the calibration

    # DECISION: countries with observations where the model doesn't produce data are ignored. Another option would 
    # be to assume they have modelled values of zero, but our data coverage is a bit patchy so this is probably a 
    # bad idea

    rp = rp.dropna(subset=['model'])
    if rp.shape[0] == 0:
        raise ValueError('No non-missing modelled values to compare to input observations.')

    return root_mean_squared_error(y_true=rp['obs'], y_pred=rp['model'], sample_weight=None)


def merge_outputs_and_obs(rp_model, rp_obs, grouping_var='country'):
    rp_model, rp_obs = deepcopy(rp_model), deepcopy(rp_obs)
    rp_model = interpolate_return_periods(rp_model, rp_obs, grouping_var=grouping_var)

    if not grouping_var:
        grouping_var = '_group_'
        rp_model[grouping_var] = 1
        rp_obs[grouping_var] = 1

    rp_model = rp_model[[grouping_var, 'rp', 'impact']].rename(columns={'impact': 'model'})
    rp_obs = rp_obs[[grouping_var, 'rp', 'impact']].rename(columns={'impact': 'obs'})

    rp_model['rank'] = rp_model.sort_values([grouping_var, 'rp'], ascending=[True, False]).groupby(grouping_var).cumcount() + 1
    rp_obs['rank'] = rp_obs.sort_values([grouping_var, 'rp'], ascending=[True, False]).groupby(grouping_var).cumcount() + 1

    # DECISION: we don't care about losses that were modelled by the pipeline but aren't present in the observations
    # This is because the criteria for inclusion in EM-DAT is kind of vague, and many event sets include events much 
    # too small for EM-DAT to find interesting, and often they will occur in the same year as an EM-DAT event, and 
    # therefore in the same footprint
    rp = pd.merge(rp_obs, rp_model, how="left", on=[grouping_var, 'rank']).rename(columns={'rp_x': 'rp'}).drop(columns=['rp_y', 'rank'])

    if grouping_var == '_group_':
        rp.drop(columns=['_group_'], inplace=True)
    return rp


# unused
def rp_rmse_choose_scale(rp_model, rp_obs, scale_bounds=[0, 1], grouping_var='country'):
    rp = merge_outputs_and_obs(rp_model, rp_obs, grouping_var)
    assert not np.any(pd.isna(rp['model']))  # There should at least be modelled zero values for every country

    # now we do some sneaky math
    scale = np.dot(rp['obs'], rp['model']) / np.dot(rp['model'], rp['model'])
    scale = np.clip(scale, scale_bounds[0], scale_bounds[1])
    errot = root_mean_squared_error(y_true=rp['obs'], y_pred=scale * rp['model'], sample_weight=None)
    return error, scale

