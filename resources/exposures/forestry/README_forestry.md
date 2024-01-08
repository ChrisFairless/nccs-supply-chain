# Forest exposure file


## Step 1: Select forests
**1. Source:** Copernicus Land Cover Map: https://cds.climate.copernicus.eu/cdsapp#!/dataset/10.24381/cds.006f2c9a?tab=overview
Description: Global map describing the land surface into 22 classes

**2. Raw file name:** "C3S-LC-L4-LCCS-Map-300m-P1Y-2020-v2.1.1.nc"

**3. Time selection:** 2020-01-01

**4. Classes chosen**:
* 50: tree_broadleaved_evergreen_closed_to_open 
* 60: tree_broadleaved_deciduous_closed_to_open 
* 61: tree_broadleaved_deciduous_closed 
* 62: tree_broadleaved_deciduous_open 
* 70: tree_needleleaved_evergreen_closed_to_open 
* 71: tree_needleleaved_evergreen_closed 
* 72: tree_needleleaved_evergreen_open 
* 80: tree_needleleaved_deciduous_closed_to_open 
* 81: tree_needleleaved_deciduous_closed 
* 82: tree_needleleaved_deciduous_open 
* 90: tree_mixed 

**3. Changes to the resolution:**
1. Raw data: 300m (lat: 64800, lon: 129600)
2. Selection for further calculations: Every 10th grid cell was selected.
3. **Final resolution:** lat: 6408, lon: 12960 (~3 km)

**4. Exposure value:** applied value=1 to all the grid cells selected based on the classes chosen.

**5. First step file name:** forest_exp_v2.h5

**6. First step jupyter notebook:** forest_exp_trial3.ipynb

**Notes:** 
1. Netcdf file available for display "f_exp.nc"
2. API requested from Copernicus:

        import cdsapi

        c = cdsapi.Client()
        
        c.retrieve(
            'satellite-land-cover',
            {
                'variable': 'all',
                'format': 'zip',
                'year': '2020',
                'version': 'v2.1.1',
            },
            'download.zip')

## Step 2: Assign region_id

**1. Files used:**

**a. input_file**: "forest_exp_v2.h5"

**b. _SHAPEFILE** = gpd.read_file("TM_WORLD_BORDERS-0.3.shp")

**2. Calculations**: 

    a. Added a column "region_id" to the input_file and assigned the ISO3 code based on _SHAPEFILE using "vectorized" funtion. 

    b. All "None" values in the region_id were removed.

**3. Second step file name:** forest_exp_region_final.h5

**4. Second step jupyter notebook:** region_id.ipynb


## Step 3: Change the exposure "value"
**1. input_file**: "forest_exp_region_final.h5"

**2. Calculations**: Applied get_forestry_exp function by CLIMADA using MRIO to assign the exposure value according to the sector 'Forestry and logging'. Function parameters used are presented below:

    exp = get_forestry_exp_new(
    countries=countries, 
    mriot_type='WIOD16',          
    mriot_year=2010,
    repr_sectors='Forestry and logging')

At each grid cell the value assigned is defined as follows:

    cnt_df['value'] = 1 / glob_prod.loc[iso3_cnt].loc[repr_sectors].sum().values[0]
       
    cnt_df['value'] = 1 / glob_prod.loc['ROW'].loc[repr_sectors].sum().values[0]
    
**3. Third step file name:** "forestry_values_MRIO.h5"

**4. Third step jupyter notebook:** exposures_forestry.ipynb

**Note:**

**IDEA:** The assigned value could be calculated as an average based on the grid cell number of each county, as defiled below:

       cnt_df['value'] = glob_prod.loc[iso3_cnt].loc[repr_sectors].sum().values[0] / len(cnt_df)
   
       cnt_df['value'] = 1 / glob_prod.loc['ROW'].loc[repr_sectors].sum().values[0] ### TO BE UPDATED

The above was tried out and saved with **file name:** "forestry_values_MRIO_avg(draft).h5"


## What can be changed:
1. **Resolution:** We may be able to increase the resolution and try with every 5th grid cell (~1.5 km). Note: this will increase the calculation time for Step 2.

2. **region_id:** Above we used _SHAPEFILE to assign the region_id. CLIMADA exposures code could be tried out to assign the region_id using target_geometries = u_coord.get_land_geometry(iso3_cnt).

3. **Exposure value:** Refer to Step 3 note idea. Method to be discussed.

4. **Climada code:** We can try to apply the CLIMADA exposure code to the raw netcdf file from Step 1. (Need to take into consideration calculation time for all countries.)








