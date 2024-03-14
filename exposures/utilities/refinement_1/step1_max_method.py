import os,sys
import pygeos
import pandas as pd
import geopandas as gpd
from pathlib import Path
from geofeather.pygeos import to_geofeather, from_geofeather
from itertools import repeat
from osgeo import gdal
import copy
gdal.SetConfigOption("OSM_CONFIG_FILE", os.path.join("../..", "osmconf.ini"))

import numpy as np
from multiprocessing import Pool,cpu_count

def set_variables():
    """Function to set the variables that are necessary as input to the model

    Returns:
        *infrastructure_systems* (dictionary): overview of overarching infrastructure sub-systems as keys and a list with the associated sub-systems as values
        *weight_assets* (dictionary): overview of the weighting of the assets per overarching infrastructure sub-system
        *weight_groups* (dictionary): overview of the weighting of the groups per overarching infrastructure sub-system
        *weight_subsystems* (dictionary): overview of the weighting of the sub-systems # this is out for our scope
    """
    # Specify which subsystems and associated asset groups need to be analyzed
    infrastructure_systems = {
                        "energy":["power"],
                        "water":["water_supply"],
                        "waste":["waste_solid","waste_water"],
                        }

    ## Set the weights of all of the infrastructure components
    weight_assets = {"energy": {"power": {"line_km": 1/7,"minor_line_km": 1/7,"cable_km": 1/7,"plant_km2": 1/7,"substation_km2": 1/7,
                                            "power_tower_count": 1/7,"power_pole_count":1/7}},

                    "water": {"water_supply": {"water_tower_km2": 1/5, "water_well_km2": 1/5, "reservoir_covered_km2": 1/5,
                                                "water_works_km2": 1/5, "reservoir_km2": 1/5}},
                    "waste": {"waste_solid": {"landfill_km2": 1/2,"waste_transfer_station_km2": 1/2},
                            "waste_water": {"wastewater_treatment_plant_km2": 1}}
                    }

    weight_groups = {"energy": {"power": 1},
                "water": {"water_supply": 1},
                "waste": {"waste_solid": 1/2,
                        "waste_water": 1/2}
                }

    weight_subsystems = {"energy": 1,
                    "water": 1,
                    "waste": 1
                         }

    return [infrastructure_systems,weight_assets,weight_groups,weight_subsystems] #weight_subsystems


def set_paths(cisi_calculation=False):

    # Set path for outputs
    base_path = "data/" #this path will contain folders in which


    infra_base_path = os.path.abspath(os.path.join(base_path, 'summary_files')) #summary amount of infrastructure saved
    method_max_path = os.path.abspath(os.path.join(base_path, 'max_method')) #final files



    return [method_max_path,infra_base_path]


def final_exposure_index(weight_subsystems, cisi_exposure, infrastructure_systems):
    """function to calculate CISI
    Arguments:
        *weight_subsystems* : dictionary containing the subsystems as keys and weight per subsystem as value
        *cisi_exposure* : dictionary consisting of a df for each subsystem holding the count, length or area per asset per grid (EPSG:4326 in Pygeos geometry)
        *infrastructure_systems* : dictionairy containing the subsystems as keys and subgroups as values

    Returns:
         pd containing the final exposure index as well as the subscores of each subsystem (columns => score and rows => the gridcell)
    """
    # Get a list of columns to be included in final exposure output
    column_names_lst = []  # , 'CISI_exposure_unnormalized']
    for ci_system in weight_subsystems:
        column_names_lst.append("Subscore_{}".format(ci_system))
    column_names_lst.append("geometry")

    # Create exposure index dataframe
    exposure_index = cisi_exposure[ci_system][[
        "geometry"]].copy()  # create dataframe to save data in by deep copying geometry of one of the subsystems --> consider using .set_index('index') to make index column the index of dataframe
    #exposure_index["CISI_exposure_unnormalized"] = 0

    # add columns to exposure_index df
    subscore_list = []  # if ci_system needs to be analyzed, save ci_system in subscore list
    for ci_system in weight_subsystems:  # loop over each CI subsystem
        # if ci_system in weight_subsystems AND in infrastructure_systems
        if ci_system in infrastructure_systems:
            exposure_index["Subscore_{}".format(ci_system)] = cisi_exposure[ci_system]["Index_{}".format(ci_system)] * (
            weight_subsystems[ci_system])  # column for subscore # changed to weight 1 to create the subscore column
            # exposure_index["CISI_exposure_unnormalized"] += exposure_index[
            #     "Subscore_{}".format(ci_system)]  # column for total score # not required since we interested in each system individually
            subscore_list.append(ci_system)
        # ci_system in weigh_subsystems BUT NOT in infrastructure_systems (i.g. ci_system is not analyzed, while included in weighting)
        else:
            exposure_index["Subscore_{}".format(ci_system)] = np.NaN

            # Normalize score between 0 and 1
    # exposure_index["CISI"] = exposure_index["CISI_exposure_unnormalized"] / exposure_index[
    #     "CISI_exposure_unnormalized"].max()

    # get subscore per infrastructure system
    # for ci_system in subscore_list:
    #     exposure_index["Subscore_{}".format(ci_system)] = exposure_index["Subscore_{}".format(ci_system)] / \
    #                                                       exposure_index["CISI_exposure_unnormalized"].max()

        # use column_names_lst to reorder columns and delete exposure_index["CISI_exposure_unnormalized"]
    exposure_index = exposure_index.reindex(columns=column_names_lst)

    return exposure_index

def cisi_overall_max_single(weight_assets, weight_groups, weight_subsystems,infrastructure_systems, cisi_exposure_base):
    """function to calculate the indices
    Arguments:
        *weight_assets* : nestled dictionary containing the subsystems as keys, followed by assetgroups, and assets. The weight per asset saved as value
        *weight_groups* : nestled dictionary containing the subsystems as keys, followed by assetgroups. The weight per assetgroup saved as value
        *weight_subsystems* : dictionary containing the subsystems as keys and weight per subsystem as value
        *infrastructure_systems* : dictionairy containing the subsystems as keys and subgroups as values
        *cisi_exposure* : dictionary consisting of a df for each subsystem holding the count, length or area per asset per grid (EPSG:4326 in Pygeos geometry)
    Returns:
        tuples containing dictionaries:
        - tuple[0]: pd containing the final exposure index based on the max of the area as well as the subscores of each subsystem (columns => score and rows => the gridcell)
        - tuple[1]: cisi_exposure with details of indices assets, groups and subsystem
    """
    print("Run calculations: calculate CISI by using max")

    cisi_exposure = copy.deepcopy(cisi_exposure_base)  # to avoid problems later on when cisi_exposure is returned
    # firstly, make indices based on assets to make the conversion to an index per groups/values
    for ci_system in infrastructure_systems:
        for value in infrastructure_systems[ci_system]:
            cisi_exposure[ci_system][
                "Index_{}".format(value)] = 0  # create column in cisi_exposure to calculate index of group
            for asset in weight_assets[ci_system][value]:
                if asset in cisi_exposure[
                    ci_system].columns:  # check whether asset in dictioniary exists in cisi exposure geodataframe
                    # conversion 1
                    if cisi_exposure[ci_system][asset].max() != 0:
                        cisi_exposure[ci_system]["Index_{}".format(asset)] = cisi_exposure[ci_system][asset]/cisi_exposure[ci_system][asset].max()
                        # add column km/max km, calculate asset index
                    else:
                        cisi_exposure[ci_system]["Index_{}".format(asset)] = 0.0
                        # conversion 2
                    cisi_exposure[ci_system]["Index_{}".format(value)] += cisi_exposure[ci_system]["Index_{}".format(asset)] * (weight_assets[ci_system][value][asset])  # assetgroup index
                else:
                    print(
                        "\033[1mNOTIFICATION: The following asset is non-existent in cisi_exposure dataframes: {} \033[0m \ncheck if extracting codes have been written correctly, otherwise, consider to exclude asset from index".format(
                            asset))

            # normalization conversion 2
            if cisi_exposure[ci_system]["Index_{}".format(value)].max() != 0:
                cisi_exposure[ci_system]["Index_{}".format(value)] = cisi_exposure[ci_system]["Index_{}".format(value)]/cisi_exposure[ci_system]["Index_{}".format(value)].max()
            else:
                cisi_exposure[ci_system]["Index_{}".format(value)] = 0.0

                # make indices based on value/groups to make the conversion to an index per system
        # conversion 3
        cisi_exposure[ci_system]["Index_{}".format(ci_system)] = 0
        for value in weight_groups[ci_system]:
            if value in infrastructure_systems[ci_system]:
                cisi_exposure[ci_system]["Index_{}".format(ci_system)] += cisi_exposure[ci_system]["Index_{}".format(value)] * (weight_groups[ci_system][value])  # calculate subsystem index

        # normalization conversion 3
        if cisi_exposure[ci_system]["Index_{}".format(ci_system)].max() != 0:
            cisi_exposure[ci_system]["Index_{}".format(ci_system)] = cisi_exposure[ci_system]["Index_{}".format(ci_system)]/cisi_exposure[ci_system]["Index_{}".format(ci_system)].max()

    # # lastly, make final exposure index based on the subsystem
    exposure_index = final_exposure_index(weight_subsystems, cisi_exposure, infrastructure_systems)

    return exposure_index

### need to understand why in their code they use cisi_exposure instead of exposure index

def cisi_calculation():
    """function to calculate the index per area (e.g. per country) using parallel processing

    Args:
        *local_path*: Local pathway. Defaults to os.path.join('/scistor','ivm','snn490').
    """

    # get settings
    infrastructure_systems,weight_assets,weight_groups,weight_subsystems= set_variables() #,

    # get paths
    method_max_path, infra_base_path = set_paths(cisi_calculation=True)

    # get cisi_exposure_base data
    # if 'cisi_exposure_base' in globals() or 'cisi_exposure_base' in locals():
    #     print("cisi_exposure_base dictionary is ready for CISI analysis")
    # else:
    #     print("Time to import the infrastructure datafiles containing the summary base calculations and put it in a dictionairy for CISI analysis")
    cisi_exposure_base = {ci_system: pd.DataFrame() for ci_system in infrastructure_systems} #use keys in infrastructure_systems to make dataframes for indices https://stackoverflow.com/questions/56217737/use-elements-in-a-list-for-dataframe-names
    #import infrastructure data of each subsystem and save in dictionary
    for ci_system in infrastructure_systems:
        if os.path.isfile(os.path.join(infra_base_path, 'summary_{}.feather'.format(ci_system))) == True: #summary_basecalcs_{}.feather
            infra_base_data = from_geofeather(os.path.join(infra_base_path, 'summary_{}.feather'.format(ci_system))) #open as geofeather #summary_basecalcs_{}.feather
            cisi_exposure_base[ci_system] = infra_base_data #save data in dictionary
        else:
            print("WARNING: the following file summary_{}.feather does not exist".format(ci_system))

    ## method 1 ##
    output_overall_max = cisi_overall_max_single(weight_assets, weight_groups, weight_subsystems,infrastructure_systems, cisi_exposure_base) # weight_subsystems,

    #Create folders for outputs (GPKGs and pngs)
    Path(method_max_path).mkdir(parents=True, exist_ok=True)
    #export as gpkg and geofeather
    to_geofeather((output_overall_max), os.path.join(method_max_path,'utilities_exposure_{}.feather'.format("all")), crs="EPSG:4326") #save as geofeather


cisi_calculation()


