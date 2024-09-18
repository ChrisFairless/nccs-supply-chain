# Observations preparation

The scripts here format observation data ready for feeding in to the calibration scripts.

Operations include
- matching events between observations and CLIMADA data
- converting event losses to return period losses
- general data wrangling

The CLIMADA calibration module takes observation data in a table form with one column per country and one row per event.

This is awkward if we're comparing hereogeneous data, so our calibration (will - TODO) reformat this to a 'long' data frame and provide a wrapper function to convert for the climada calibration.