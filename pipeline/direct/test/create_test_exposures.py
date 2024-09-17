import numpy as np
import geopandas as gpd
from climada.entity.exposures.base import Exposures

# Create simple hazard objects for testing
# Adapted from the CLIMADA testing suite (originally called good_exposures)

def test_exposures():
    """Followng values are defined for each exposure"""
    data = {}
    data['latitude'] = np.array([1, 2, 3])
    data['longitude'] = np.array([2, 3, 4])
    data['value'] = np.array([1, 2, 3])
    # data['deductible'] = np.array([1, 2, 3])
    data['impf_TC'] = np.array([1, 1, 1])
    # data['category_id'] = np.array([1, 2, 3])
    data['region_id'] = np.array([1, 2, 3])
    # data['centr_TC'] = np.array([1, 2, 3])

    exp = Exposures(gpd.GeoDataFrame(data=data))
    return exp