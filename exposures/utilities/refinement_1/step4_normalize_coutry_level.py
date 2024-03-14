import pandas as pd

subscores = ["Subscore_energy", "Subscore_water", "Subscore_waste"]

for subscore in subscores:

    data = pd.read_hdf(f"data/{subscore}_ISO3.h5")  # file from step 4 excluding national parks and protected areas
    countries = data["region_id"].unique().tolist()
    countries.sort()

    cnt_dfs = []

    for iso3_cnt in countries:
        cnt_df = data.loc[data['region_id'] == iso3_cnt].copy()

        cnt_df.loc[:, "country_normalized"] = cnt_df[subscore] / cnt_df[subscore].max() # normalize by max value

        cnt_dfs.append(cnt_df)

    df = pd.concat(cnt_dfs).reset_index(drop=True)


    df.to_hdf(f"data/{subscore}_ISO3_normalized.h5", key="df", mode="w")

