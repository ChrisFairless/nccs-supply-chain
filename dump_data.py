import pickle
import pandas as pd

with open('analysis_df.pkl', 'rb') as f:
    analysis_df = pickle.load(f)

df_indirect = []
for (i, row) in analysis_df.iterrows():
    df_indirect.extend(
        [
            {
                "sector": sec,
                "value": v,
                "hazard_type": row['haz_type'],
                "country_of_impact": row['country']
            }
            for (sec, v) in row['supchain'].tot_prod_impt_eai.loc[('CHE', slice(None))].items()
        ]
    )


df_indirect = pd.DataFrame(df_indirect)
df_indirect.to_csv('results/indirect_impacts.csv')