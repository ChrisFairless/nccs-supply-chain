# Utilities Exposure 

**Data source:** Nirandjan, Sadhana, et al. "A spatially-explicit harmonized global dataset of critical infrastructure." Scientific Data 9.1 (2022): 150. (https://www.nature.com/articles/s41597-022-01218-4)

 -> under the license: Creative Commons Attribution 4.0 International License

**Link to directly download the data:** https://zenodo.org/records/4957647
- Files downloaded under the **resolution 0.1x0.1 degree**, representing total amount of each infrastructure type within a given grid cell: 
  - `summary_energy.feather` 
  - `summray_water.feather`
  - `summary_waste.feather`



**Calculation Steps**

- Step 1: Normalize the amount of infrastructure of each sector similarly to the application performed by Nirandjan et al. 2022, up until the method "Conversion 3". The normalization is performed at global scale. Code: https://github.com/Correntics/nccs-correntics/blob/main/utilities/step1_max_method.py
- Step 2: Convert normalized feather files of each sector to h5 files. In the steps we introduce the columns lat, lon by taking the centroid value of the polygons provided by the initial feather files. Finally, we remove rows where the amount of infrastructure is zero at the given point(/grid). Code: https://github.com/Correntics/nccs-correntics/blob/main/utilities/step2_convert_feather_files.py
- Step 3: Assign for each row (lat/lon location) a country ISO code that is needed by the Climada SupplyChain module. Code: https://github.com/Correntics/nccs-correntics/blob/main/utilities/step3_region_ID.py
- Step 4: At this step we create a new column "normalized_country", where the Subscore of given sector is normalized at country level following the maximum method (i.e. divide the values by the maximum value of the country). Code: https://github.com/Correntics/nccs-correntics/blob/main/utilities/step4_normalize_country_level.py
- Step 5: Assign for each datapoint a value according to the total production of each sector within a country : 
  - Assign the mriot value of each sector and multiply it with the normalized factor of the country. Code: https://github.com/Correntics/nccs-correntics/blob/main/utilities/step5_MRIO_values.py
   ```
   # Total value per country based on:
    mriot_type='WIOD16',
    mriot_year=2011,
    if subscore == "Subscore_energy":
        repr_sectors = "Electricity, gas, steam and air conditioning supply"

    elif subscore == "Subscore_water":
        repr_sectors = "Water collection, treatment and supply"

    elif subscore == "Subscore_waste":
        repr_sectors = "Sewerage; waste collection, treatment and disposal activities; materials recovery; remediation activities and other waste management services"

  data = pd.read_hdf(f"data/{subscore}_ISO3_normalized.h5") # this is the file created in step 4
        
  ROW_gdp_lookup = get_ROW_factor_GDP(mriot_year, IO_countries, countries)
      
  for iso3_cnt in countries:

    cnt_df = data.loc[data['region_id'] == iso3_cnt]
    
    try:
        cnt_df['value'] = glob_prod.loc[iso3_cnt].loc[repr_sectors].sum().values[0] * cnt_df["country_normalized"]
    except KeyError:
          LOGGER.warning('You are simulating a country for which there are no production data in the chosen IOT')
             
          # code under option 2:
          try:
              ROW_gdp_factor = ROW_gdp_lookup.loc[ROW_gdp_lookup['Country Code'] == iso3_cnt, 'Normalized_GDP'].values[0]
              ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_gdp_factor)
              cnt_df['value'] = ROW_country_production * cnt_df["country_normalized"]
          except:
              print(f"For the country {iso3_cnt} there is no GDP value available, 0 value is assigned")
              ROW_gdp_factor = 0
              ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_gdp_factor)
              cnt_df['value'] = ROW_country_production * cnt_df["country_normalized"]

  cnt_dfs.append(cnt_df)


**Limitations/considerations**
-
- The data is provided at a resolution of 0.1x0.1 degree. Even though each gird cell represent the factor amount of infrastructure within the given cell, the whole grid cell is exposed.
- ROW countries that are not included in the GDP list are assigned with a value of 0.


**Visual: Plots on normalized data by country for each sector**
![Subscore_energy_cnormalized.png](data%2FSubscore_energy_cnormalized.png)
![Subscore_water_cnormalized.png](data%2FSubscore_water_cnormalized.png)
![Subscore_waste_cnormalized.png](data%2FSubscore_waste_cnormalized.png)

**Visual: Plots with MRIO value**
![Subscore_energy_MRIO.png](data%2FSubscore_energy_MRIO.png)
![Subscore_waste_MRIO.png](data%2FSubscore_waste_MRIO.png)
![Subscore_water_MRIO.png](data%2FSubscore_water_MRIO.png)