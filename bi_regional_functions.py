import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv(r'C:\github\nccs-supply-chain\resources\impact_functions\business_interruption\FL_HAZUS_BI_industry_modifiers.csv')

# Convert rows to columns
df = df.T

df = df.replace(0, 0.0001)
# first row as header
new_header = df.iloc[0] #grab the first row for the header
df = df[1:] #take the data less the header row
df.columns = new_header #set the header row as the df header

# plot the columns take the first column as x-axis as line plot for each colum a line
plt.figure()
df.plot()
plt.ylim(0, 1.2)
plt.show()

#Factors with flood protection
regional_factors = {
    "Africa": 0.22,
    "Asia": 0.18,
    "Europe": 0.27,
    "North America": 0.15,
    "Oceania": 0.1,
    "South America": 0.061
}
factor_sectors = ["Manufacturing", "Utilities", "Service"]

# Select the columns that are in the factor_sectors
subdf = df[df.columns.intersection(factor_sectors)]
mean_factors = subdf.mean(axis=1)

plt.figure()
mean_factors.plot()
plt.ylim(0, 1.2)
plt.show()

# divide the columns by the mean
mean_to_sectors = df.copy()
for col in mean_to_sectors.columns:
    mean_to_sectors[col] = mean_to_sectors[col] / mean_factors

# define a mapping factor connecting HAZUS data with North America
mapping_us_hazus_to_regional = mean_factors / regional_factors["North America"] # since we assume hazus is for North America and provides the link

# Plot regional means
fig = plt.figure()
for region in regional_factors:
    df_region = mapping_us_hazus_to_regional * regional_factors[region]
    df_region.plot(legend=True)
plt.legend(regional_factors.keys())
plt.title("Mean sector scaled per region")
plt.ylim(0, 1.2)
plt.show()

# plot individual sectors per region
for region in regional_factors:
    fig = plt.figure()
    for sector in df.columns:
        df_sector = mean_to_sectors[sector] * mapping_us_hazus_to_regional * regional_factors[region]
        df_sector.plot(legend=True)
    plt.legend(df.columns)
    plt.title(region)
    plt.ylim(0, 1.2)
    plt.show()

#Todo remove agriculture from the plot as it is not being used within the pipeline --> Agriculture does not get a sector scaling, as the loss is already in crop loss

#TODO extract a reduction factor for each region/ sector that can be used in the pipeline
# or actually, save those curves per region and recall them for each country using a region mapping 








