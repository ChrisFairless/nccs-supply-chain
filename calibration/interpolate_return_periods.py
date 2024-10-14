import numpy as np
import logging
import pandas as pd

LOGGER = logging.getLogger(__name__)


# Method to take two dataframes of losses by return period and country/group and interpolate
# the losses of the first to match the return periods of the second (by country/group)

def interpolate_return_periods(rp_input, rp_target, grouping_var='country', left=np.nan, right=np.nan):
    output = []
    if not grouping_var:
        grouping_var = '_group_'
        rp_input['_group_'] = 1
        rp_target['_group_'] = 1

    for group in rp_target[grouping_var].unique():
        rp_input_group = rp_input.loc[rp_input[grouping_var] == group]
        rp_input_group = rp_input_group[[grouping_var, 'rp', 'impact']].sort_values(['rp'], ascending=True)
        rp_target_group = rp_target.loc[rp_target[grouping_var] == group]
        rp_target_group = rp_target_group[[grouping_var, 'rp', 'impact']].sort_values(['rp'], ascending=True)

        # Deal with no modelled impacts
        if rp_input_group.shape[0] == 0:
            output.append(
                pd.DataFrame({
                    grouping_var: group,
                    'rp': rp_target_group['rp'],
                    'impact': np.nan
                })
            )
        
        else:
            output.append(
                pd.DataFrame({
                    grouping_var: group,
                    'rp': rp_target_group['rp'],
                    'impact': np.interp(
                        x = np.array(rp_target_group['rp']),
                        xp = np.array(rp_input_group['rp']),
                        fp = np.array(rp_input_group['impact']),
                        left=left,
                        right=right
                    )
                })
            )
    
    rp = pd.concat(output)

    missing_groups_all_df = rp.groupby(grouping_var)[['impact']].apply(lambda x: x.isnull().all())
    missing_groups_any_df = rp.groupby(grouping_var)[['impact']].apply(lambda x: x.isnull().any())
    missing_groups_all = missing_groups_all_df[missing_groups_all_df['impact'] > 0].index.tolist()
    missing_groups_any = missing_groups_any_df[missing_groups_any_df['impact'] > 0].index.tolist()
    if len(missing_groups_all) > 0:
        LOGGER.warning(f'The cost calculation had no modelled reproductions of observations for {len(missing_groups_all)} groups: {missing_groups_all}')
    elif len(missing_groups_any) > 0:
        LOGGER.warning(f'The cost calculation had missing modelled reproductions of observations for {len(missing_groups_any)} groups: {missing_groups_any}')

    if grouping_var == '_group_':
        rp.drop(columns=['_group_'], inplace=True)

    return rp