import numpy as np
import logging
import pandas as pd

LOGGER = logging.getLogger(__name__)


# Method to take two dataframes of losses by return period and country and interpolate
# the losses of the first to match the return periods of the second (by country)

def interpolate_return_periods(rp_input, rp_target, left=np.nan, right=np.nan):
    output = []
    for country in rp_target['country'].unique():
        rp_input_country = rp_input.loc[rp_input['country'] == country]
        rp_input_country = rp_input_country[['country', 'rp', 'impact']].sort_values(['rp'], ascending=True)
        rp_target_country = rp_target.loc[rp_target['country'] == country]
        rp_target_country = rp_target_country[['country', 'rp', 'impact']].sort_values(['rp'], ascending=True)

        # Deal with no modelled impacts
        if rp_input_country.shape[0] == 0:
            raise ValueError(f'Need to deal with no modelled events . Country {country}')
        
        output.append(
            pd.DataFrame(dict(
                country = country,
                rp = rp_target_country['rp'],
                impact = np.interp(
                    x = np.array(rp_target_country['rp']),
                    xp = np.array(rp_input_country['rp']),
                    fp = np.array(rp_input_country['impact']),
                    left=left,
                    right=right
                )
            ))
        )
    
    # print('output')
    # print(output)
    return pd.concat(output)