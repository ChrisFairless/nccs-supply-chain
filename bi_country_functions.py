import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv(r'C:\github\nccs-supply-chain\resources\impact_functions\business_interruption\FL_HAZUS_BI_industry_modifiers.csv')
#Output of the optimization
country_factors = pd.read_csv(r"C:\github\nccs-supply-chain\results\bi-calibration-results_test_without.csv")

# Convert rows to columns
df = df.T

df = df.replace(0, 0.0001)
# first row as header
new_header = df.iloc[0] #grab the first row for the header
df = df[1:] #take the data less the header row
df.columns = new_header #set the header row as the df header

# Convert the index to numeric
df.index = pd.to_numeric(df.index)
# Overwrite the Agriculture column with the index values
df['Agriculture'] = df.index

# plot the columns take the first column as x-axis as line plot for each colum a line
plt.figure()
df.plot()
plt.ylim(0, 1.2)

plt.show()

# mapping from country_factors sector to df Industry Type columns
sector_mapping = {
    'forestry': ['Forestry'],
    'mining': ['Mining (Processing)'],
    'energy': ['Utilities'],
    'service': ['Service'],
    'manufacturing': ['Manufacturing']
}

scaled_dfs = {}

# Apply scaling for each country
for _, row in country_factors.iterrows():
    country = row['country']
    sector = row['sector']
    scaling_factor = row['scale']

    # sector_mapping to find the matching column in df
    if sector in sector_mapping:
        industry_columns = sector_mapping[sector]

        # only if the country does not exist
        if country not in scaled_dfs:
            scaled_dfs[country] = df.copy()

        for industry_column in industry_columns:
            scaled_dfs[country][industry_column] *= scaling_factor

# make the it again to numbers
for country in scaled_dfs.keys():
    scaled_dfs[country].index = pd.to_numeric(scaled_dfs[country].index)


# Plotting
for country, scaled_df in scaled_dfs.items():
    plt.figure()
    for column in scaled_df.columns:
        plt.plot(scaled_df.index, scaled_df[column], label=column)

    plt.title(f'Scaled Functions for {country}')
    plt.xlabel('x')
    plt.ylabel('y (scaled)')
    plt.ylim(0, 1.2)

    # plt.xlim(0, 1.2)

    plt.legend()
    plt.show()

#Todo Save the scaled_dfs somewhere or include scalding for the sectors