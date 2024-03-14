### Manufacturing Exposure 

**Data source:** EDGAR Annual Sector-specific Gridmaps: 

 -> Under the license: Unless otherwise indicated (e.g. in individual copyright notices), content owned by the EU on this website is licensed under the Creative Commons Attribution 4.0 International (CC BY 4.0) license. This means that reuse is allowed, provided appropriate credit is given and changes are indicated.

Description: Emission grid maps are expressed in t substance/0.1degreex0.1degree/year for the .txt files 

**Link to directly download the data:**

- Food and paper NOx:  https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v61_AP/NOx/FOO_PAP/EDGARv6.1_NOx_2011_FOO_PAP.zip, Raw data look:https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v61_AP/gallery/NOx/FOO_PAP/EDGARv6.1_NOx_2011_FOO_PAP.png 
- Oil refineries & Transformation industry NOx: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v61_AP/PM2.5/REF_TRF/EDGARv6.1_PM2.5_2011_REF_TRF.zip, raw data look: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v61_AP/gallery/NOx/REF_TRF/EDGARv6.1_NOx_2011_REF_TRF.png 
- Chemical we used NMVOC emissions, separate documentation on shared folder: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v61_AP/NMVOC/CHE/EDGARv6.1_NMVOC_2011_CHE.zip, raw data look: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v61_AP/gallery/NMVOC/CHE/EDGARv6.1_NMVOC_2011_CHE.png
- non-metallic-mineral-production: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v61_AP/PM10/NMM/EDGARv6.1_PM10_2011_NMM.zip, view raw data: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v61_AP/gallery/PM10/NMM/EDGARv6.1_PM10_2011_NMM.png
- Basic Metals: a special approach has to be conducted for this sector since EDGAR has the iron and steel production separate from the non-ferrous-metal production. But both are part of the basic metal sector: Therefore, we used the C:\github\nccs-correntics\manufacturing\manufacturing_sub_exposures\Step_special_combine_basic_metals.py script, to first combine the iron and steel and non-ferrous datasets by merging them and summing up emission values which for which the geometries are equal. 150 rows were equal and leaves us with 61285 rows for this sector. Iron and Steel data: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v61_AP/CO/IRO/EDGARv6.1_CO_2011_IRO.zip, raw data view: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v61_AP/gallery/CO/IRO/EDGARv6.1_CO_2011_IRO.png & Non-ferrous metals: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v61_AP/CO/NFE/EDGARv6.1_CO_2011_NFE.zip, with view raw data https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v61_AP/gallery/CO/NFE/EDGARv6.1_CO_2011_NFE.png
- Pharmaceutical: NMVOC of chemical: separate documentation on shared folder: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v61_AP/NMVOC/CHE/EDGARv6.1_NMVOC_2011_CHE.zip, raw data look: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v61_AP/gallery/NMVOC/CHE/EDGARv6.1_NMVOC_2011_CHE.png
  - Alternative would be to use annual NOx as general production loctaions, but then I get less hubs
- wood: no explicit sector exposure --> total annual NOx scaled: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v61_AP/NOx/TOTALS/EDGARv6.1_NOx_2011_TOTALS.zip
- rubber and plastic -->no explicit sector exposure --> total annual NOx scaled: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v61_AP/NOx/TOTALS/EDGARv6.1_NOx_2011_TOTALS.zip
**Calculation Steps**

- Step 1: Convert the txt file to a data frame (several EDGAR emission data sets can be selected together:
  - There is the option to choose an emission value above which it gets selected
  - At the moment the threshold is set to 0 for exposures with an explicit sectorial emission since a lot of rows (and thus locations) have a very low emission. Applying the 100t rule, for instance, would leave us with only 200 food locations. 100t threhsold rule was however applied to exposures that are scaled from the annual total emissions of NOx, as no explicit exposure available
  - Food: 192874 points
  - refin_and_transform: 294006 points
  - chemical: 216274 points
  - non-metallic-mineral: 269384 points
  - basic metals: 61285 points
  - pharmaceutical; 216274 points,
  - wood: 163135 points (above 100t, since all points are considered which have NOx),
  - rubber and plastic: 163135 points (above 100t, since all points are considered which have NOx)

- Step 2: Assign for each row (lat/lon location) a country ISO code that is needed by the Climada SupplyChain module:
  - Food: has 8796 rows where no country could be assigned, still 184078 (mostly in ocean)
  - Oil and refinery: has 12038 points where no country could be assigned but still 281968 left (mostly in ocean)
  - Chemical: 9654 unassigned points (in the ocean), where no country could be assigned, still 206620 left (mostly in ocean)
  - non-metallic mineral:11631 unassigned points (in the ocean), where no country could be assigned, still 257754 left (mostly in ocean)
  - basic metals: 1522 unassigned points (in the ocean), where no country could be assigned, still 59763 left (mostly in ocean)
  - pharmaceutical: 9654 unassigned points (in the ocean), where no country could be assigned, still 206620 left (mostly in ocean)
  - wood: 29438: unassigned points (in the ocean), where no country could be assigned, still 133697 points lefts
  - ruber and plastic: unassigned points (in the ocean), where no country could be assigned, still 133697 points lefts

- Step 3: Assign for each datapoint a value according to the total production of each sector within a country and the amount of emissions per grid cell: 
  - At the moment we use the ROW countries for the general manufacturing production for the scaling and not sector-specific production. Some data would be available but there are a lot of countries missing
  - Therefore, a lot of ROW countries would get assigned a 0 value even though they report emissions
  - For food:
  - For Chemical:
  - For refinery and transform:
  - For non-metallic minerals: No values in the manufacturing production data set: AIA, ALA, ANT, CXR, ESH, FLK, GLP, GUF, JEY, MTQ, REU
  - For basic metals: 93 countries with basic metal exposure, all countries could be assigned
  - For pharmaceuticals: 140 countries with "pharmaceutical" exposure, not asigned countries: ALA, GUF
  - For wood: 208 countries: same as for general NOx not assigned
  - For rubber and plastics




**Exposure Properties**
-0.1 x 0.1 deg 
- Food and Paper:![food_and_paper_NOX_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled.png](intermediate_data_EDGAR%2Ffood_and_paper_NOX_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled.png)
- Oil refinery and Tranformation:![refin_and_transform_NOx_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled.png](intermediate_data_EDGAR%2Frefin_and_transform_NOx_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled.png)
- Chemical Process: ![chemical_process_NMVOC_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled.png](intermediate_data_EDGAR%2Fchemical_process_NMVOC_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled.png)
- Non-metallic minreals: ![non_metallic_mineral_PM10_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled.png](intermediate_data_EDGAR%2Fnon_metallic_mineral_PM10_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled.png)
- basic metals: ![basic_metals_CO_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled.png](intermediate_data_EDGAR%2Fbasic_metals_CO_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled.png)
- pharmaceutical:![pharmaceutical_NMVOC_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled.png](intermediate_data_EDGAR%2Fpharmaceutical_NMVOC_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled.png)
- wood: ![wood_NOx_emissions_2011_above_100t_0.1deg_ISO3_values_Manfac_scaled.png](intermediate_data_EDGAR%2Fwood_NOx_emissions_2011_above_100t_0.1deg_ISO3_values_Manfac_scaled.png)
- rubber and plastics:![rubber_and_plastic_NOx_emissions_2011_above_100t_0.1deg_ISO3_values_Manfac_scaled.png](intermediate_data_EDGAR%2Frubber_and_plastic_NOx_emissions_2011_above_100t_0.1deg_ISO3_values_Manfac_scaled.png)


- The **final file** after step: 
  - Food and Paper:food_and_paper_NOx_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled.h5
  - Oil refinery: refin_and_transform_NOx_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled.h5
  - Chemical process: chemical_process_NMVOC_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled.h5
  - Non-metallic-mineral: non_metallic_mineral_PM10_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled.h5
  - Basic metals: basic_metals_CO_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled.h5
  - pharmaceutical: pharmaceutical_NMVOC_emissions_2011_above_0t_0.1deg_ISO3_values_Manfac_scaled.h5
  - wood:wood_NOx_emissions_2011_above_100t_0.1deg_ISO3_values_Manfac_scaled.h5
  - rubber and plastic:rubber_and_plastic_NOx_emissions_2011_above_100t_0.1deg_ISO3_values_Manfac_scaled.h5
**Exposure Validation**
- Oil refinery and Transformation: https://www.epa.gov/sites/default/files/2016-11/documents/refineries_2013_112516.pdf, https://www.petro-online.com/news/biofuel-industry-news/22/breaking-news/which-countries-have-the-largest-oil-refinery-capacity/54409

**Potential Improvements**
- set thresholds of emissions to a level to not consider all the small points (even though the emissions have been reported per sector)

**Limitations**

-What about including several emissions and not only NOx, combine them in a meaningful way? As NOx might not be ideal for all of them?
-Asked EDGAR team on any hints about this topic...


