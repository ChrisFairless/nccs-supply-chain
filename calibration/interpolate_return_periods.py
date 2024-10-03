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
            output.append(
                pd.DataFrame(dict(
                    country = country,
                    rp = rp_target_country['rp'],
                    impact = np.nan
                ))
            )
        
        else:
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
    
    rp = pd.concat(output)

    missing_countries_all_df = rp.groupby('country')[['impact']].apply(lambda x: x.isnull().all())
    missing_countries_any_df = rp.groupby('country')[['impact']].apply(lambda x: x.isnull().any())
    missing_countries_all = missing_countries_all_df[missing_countries_all_df['impact'] > 0].index.tolist()
    missing_countries_any = missing_countries_any_df[missing_countries_any_df['impact'] > 0].index.tolist()
    if len(missing_countries_all) > 0:
        LOGGER.warning(f'The cost calculation had no modelled reproductions of observations for {len(missing_countries_all)} countries: {missing_countries_all}')
    elif len(missing_countries_any) > 0:
        LOGGER.warning(f'The cost calculation had missing modelled reproductions of observations for {len(missing_countries_any)} countries: {missing_countries_any}')

    return rp