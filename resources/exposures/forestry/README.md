# Forest exposure file

#### Data:
**Source:** Copernicus Land Cover Map: https://cds.climate.copernicus.eu/cdsapp#!/dataset/10.24381/cds.006f2c9a?tab=overview
  
**Time selection:** 2020-01-01

**Description:**
1. Global maps describing the land surface into 22 classes
2. **Classes chosen**:
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


**Resolution:**
1. Raw data: 300m (lat: 64800, lon: 129600)
2. **Selection**: Every 10th grid cell was selected.
3. **Final resolution:** lat: 6408, lon: 12960

**Final file name:** forest_exp_v2.h5

**Notes:** 
1. Netcdf file available for display "f_exp.nc".
2. Version 1 was also including "100: mosaic_tree_and_shrub" but this was decided to be removed.
3. API requested from Copernicus:

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

