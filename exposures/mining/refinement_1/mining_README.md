### Mining Exposure 

**Data source:** [Maus, V et al. (2022): Global-scale mining polygons (Version 2) (pangaea.de)](https://doi.pangaea.de/10.1594/PANGAEA.942325)https://doi.pangaea.de/10.1594/PANGAEA.942325

 -> under the license: https://creativecommons.org/licenses/by-sa/4.0/

Maus et al. (2022): global-scale mining area: Using visual interpretation of Sentinel-2 images for 2019, we inspected more than 34,000 mining locations across the globe. The data was derived using a similar methodology as the first version by visual interpretation of satellite images. The study area was limited to a 10 km buffer around the 34,820 mining coordinates reported in the S&P metals and mining database. We digitalized the mining areas using the 2019 Sentinel-2 cloudless mosaic with 10 m spatial resolution (https://s2maps.eu by EOX IT Services GmbH - Contains modified Copernicus Sentinel data 2019). We also consulted Google Satellite and Microsoft Bing Imagery, but only as additional information to help identify land cover types linked to the mining activities. 

The result is a global-scale dataset containing 44,929 polygon features covering 101,583 km2 of large-scale as well as artisanal and small-scale mining. The polygons cover all ground features related to mining, .e.g open cuts, tailing dams, waste rock dumps, water ponds, processing infrastructure, and other land cover types related to the mining activities. 

**Link to directly download the data:** https://doi.pangaea.de/10.1594/PANGAEA.942325?format=html#download

Where we downloaded the following file:

- global_miningarea_v2_30arcsecond.tif (approximately 1x1 km at the equator) that contains Grid datasets with the mining area in squared kilometers per cell derived from the mining polygons.**


**Calculation Steps**

- Step 1: Convert the tif file into a netcdf: https://github.com/Correntics/nccs-correntics/blob/main/mining/preprocess_raw_files/Step1_MAUS_tif_to_nc.py
- Step 2: Convert the nc file to a data frame: https://github.com/Correntics/nccs-correntics/blob/main/mining/preprocess_raw_files/Step2_MAUS_convert_nc_to_dataframe.py
- Step 3: Assign for each row (lat/lon location) a country ISO code that is needed by the Climada SupplyChain module:https://github.com/Correntics/nccs-correntics/blob/main/mining/preprocess_raw_files/Step3_MAUS_assignISO3codes.py
- Step 4: Assign for each datapoint a value according to the total production of each sector within a country and the amount of area of mining per gridcell: https://github.com/Correntics/nccs-correntics/blob/main/mining/preprocess_raw_files/Step4_MAUS_assign_value.py
  - First: Normalize the area within each gridcell by dividing the mining area by the total area of mines per country:
    ```
    #calculate total area of mines per country
    country_sum_area = cnt_df['area'].sum()

    # Normalize 'area' values by dividing by total area
    cnt_df['normalized_area'] = cnt_df['area'] / country_sum_area

   
  - Second: Assign the mriot Mining and Quarrying production value and multiply it with the normalized area
   ```
   # Total value per country based on:
   # mriot_type='WIOD16',
   # mriot_year=2011,
   # repr_sectors='Mining and quarrying'
   
   # For countries that are explicitly in the MRIO  table:
   cnt_df['value'] = cnt_df['normalized_area'] * (glob_prod.loc[iso3_cnt].loc[repr_sectors].sum().values[0])

   #For Rest of the world countries: *ROW scaling according to WorldMiningData
   
  ### New Option Option 3: scale the ROW MRIO value according to WorldMinind Data total mineral Production

    #load the MP (mineral production) of countries
    WorldMiningData = pd.read_excel(r'C:\github\nccs-correntics\mining\preprocess_raw_files\WorldMiningData_2021_Total_Mineral_Production.xlsx')

    # Select only the specified year column and filter rows based on the 'Country Code',
    # select only the countries with are not within the IO table
    ROW_MiningProd = WorldMiningData[['ISO3','Total Value Mineral Production (incl. Bauxite)']][~WorldMiningData['ISO3'].isin(IO_countries)]
    # select only the countries which are in the countries list (and not in the IO from before)
    filtered_MiningProd = ROW_MiningProd[ROW_MiningProd['ISO3'].isin(countries)]

    ROW_total_prod = filtered_MiningProd['Total Value Mineral Production (incl. Bauxite)'].sum()
    # Create a new column with normalized GDP values
    filtered_MiningProd['Normalized_Prod'] = filtered_MiningProd['Total Value Mineral Production (incl. Bauxite)'] / ROW_total_prod
    return filtered_MiningProd
   
  Within the country loop:
  ROW_mineral_prod_factor = ROW_mineral_prod.loc[ROW_mineral_prod['ISO3'] == iso3_cnt, Normalized_Prod'].values[0]
  ROW_country_production = ((glob_prod.loc['ROW'].loc[repr_sectors].sum()).values[0] * ROW_mineral_prod_factor)
  cnt_df['value'] = cnt_df['normalized_area'] * ROW_country_production
  print(f"For the country {iso3_cnt} there is no MP value available, 0 value is assigned")




**Exposure Properties**
- The file has actually quite a high resolution of 1kmx1km
- The value is assessed using the MRIO table and is in the unit of millions USD (same as the MRIO table). Like this, the exposed value is a "production value" at risk and not an "asset value" at risk. 
- Exposure using the mean value as a colormax (values are given in M.USD), please note that the point size is quite big and that the real data is much sparser
- ![global_miningarea_v2_30arcsecond_converted_ISO3_improved_values_MP_scaled.png](intermediate_data_MAUS%2Fglobal_miningarea_v2_30arcsecond_converted_ISO3_improved_values_MP_scaled.png)

- The **final file** after step 4 is currently: **global_miningarea_v2_30arcsecond_converted_ISO3_improved_values_MP_scaled.h5** ("global_miningarea_v2_30arcsecond_converted_ISO3_improved_values_GDP_scaled.h5" would be for the GDP version)
- Additionally, to check the exposure in QGIS, we also save a shapefile

**Potential Improvements**
- Coarsening of data to lower resolution depending on the resolution of the hazards
- Open question: If we use another MRIO table for the supply chain calculation, would we also need to rerun the value distribution of this mining exposure with the new MRIO table?



**Limitations**
- No information about any product groups (e.g. Gold, Silver ect.)
   - Justification: Is okay, since there is no product information within the MRIO table, we would thus not further benefit largely from this information
- No differentiation between the considered mining activities (e.g. open cuts, tailings dams, waste rock dumps, water ponds, processing plants, and other ground features related to the mining activities)
- No adequate representation of underground mines (due to satellite data)
   - Justification: Most likely, underground mines are also less affected by hazards (except maybe streets that lead to underground mines)
- Equality of mining locations: Value distribution does not consider if it is a gold or a coal mine. Value distribution purely depends on the area per grid cell of mining activity and the production value of the mining sector within a given country
- GDP approach (not in use): For only a few countries, there was no GDP according to which the values could be scaled (for ESH= Westsahara, SJM= Svalbard, and GUF= Französisch-Guayana)
- Mineral Production Approach (active in use): For only a few countries with also a rather small mining area, there are no mineral production values from the table: Aruba (ABW), ESH = Westsahara, GNB = Guinea Bissau, GRL = Greenland, HTI = Haiti, LSO = Lesotho, PKR (North Korea), SJM = Svalbard, SOM= Somalia), 

**ROW-scaling MRIO value according to Mineral Production of WorldMiningData (Remark to Step 4 within calculation)**
- Since we use the MRIO table values to disaggregate the value per country according to the mining area of each point, we need to have information for the countries that are not explicitly listed within the MRIO table (ROW countries)
- Therefore, we use the WorldMiningData where we get the total mineral production for each country
- Source: https://www.world-mining-data.info/?World_Mining_Data___Data_Section
- The data is license-free, similar to BSG and USGS data and we need to provide a citation. Check again on the website how the citation needs to be done.
- WorldMiningData, mineral production accounts for the following raw materials:
<img width="446" alt="image" src="https://github.com/Correntics/nccs-correntics/assets/116871277/48ba02c3-e1d1-48c4-9628-bdbaa5797810">

 


**Mining within the WIOD table**
- General reference which needs to be used when using the WIOD16 (https://www.rug.nl/ggdc/valuechain/wiod/wiod-2016-release) release: https://onlinelibrary.wiley.com/doi/10.1111/roie.12178
- from this reference, we get the ISIC rev.3 code for the Mining and quarrying sector: C
- Within this document: [https://unstats.un.org/unsd/statcom/doc02/isic.pdf](https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/ISIC_Rev_4_publication_English.pdf), we can get information on which subsectors actually are considered within the Mining and quarrying sector according to the definition
- <img width="788" alt="image" src="https://github.com/Correntics/nccs-correntics/assets/116871277/b000a04b-99bf-4165-a609-f2989f869e89">

