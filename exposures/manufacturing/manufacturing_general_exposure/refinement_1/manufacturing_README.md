### Manufacturing Exposure 

**Data source:** EDGAR Annual NOx Gridmaps: https://edgar.jrc.ec.europa.eu/gallery?release=v61_AP&substance=NOx&sector=TOTALS

 -> under the license: Unless otherwise indicated (e.g. in individual copyright notices), content owned by the EU on this website is licensed under the Creative Commons Attribution 4.0 International (CC BY 4.0) licence. This means that reuse is allowed, provided appropriate credit is given and changes are indicated.

Description: Emission gridmaps are expressed in t substance/0.1degreex0.1degree/year for the .txt files 

**Link to directly download the data:** https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v61_AP/NOx/TOTALS/EDGARv6.1_NOx_2011_TOTALS.zip
Where we downloaded the following file: 2011 EDGARv6.1_NOx_2011_TOTALS.zip
![img_1.png](img_1.png)

- 

**Calculation Steps**

- Step 1: Convert the txt file to a data frame:
  - we took the emission of the year 2011 with a 0.1deg resolution, which has 4462102 rows of gridcell points
  - we removed all the emissions below 100t per year (such as in Tobler 2018) and ended up with 163135 data points
- Step 2: Assign for each row (lat/lon location) a country ISO code that is needed by the Climada SupplyChain module:
  - For a total of 29438 rows (gridpoints) no country could be assigned, and they have been deleted, which leaves us with 133697 gridcells
  - In Total, we have 208 countries listed that have NOx emssions > 100t per year 
- Step 3: Assign for each datapoint a value according to the total production of each sector within a country and the amount of area of mining per gridcell: 
  - No value could be assigned for the following countries: AIA, ANT, CRX, ESH, FLK, GUF, IOT, MSR, REU, SJM
  - All the manufacturing subsectors of WIOD were summed up and taken as a total country value to distribute according to signal
  



**Exposure Properties**
-0.1 x 0.1 deg resolution
- with 133697 entry points within 208 countries
- Manufactuirng exposures per country based on sclaing with NOx emissions and production values: Largest contributors: China, USA, Japan, Germany, Korea, India, Brazil, Italy, France (Top List in agreement with Worlbank manufacuirng exports)
      


- The **final file** after step: **global_noxemissions_2011_above_100t_0.1deg_ISO3_values_Manfac_scaled.h5**
![global_noxemissions_2011_above_100t_0.1deg_ISO3_values_Manfac_scaled.png](intermediate_data_EDGAR%2Fglobal_noxemissions_2011_above_100t_0.1deg_ISO3_values_Manfac_scaled.png)![img.png](img.png)
**Potential Improvements**
- 

**Limitations**
-



**Manufacturing within the WIOD table
