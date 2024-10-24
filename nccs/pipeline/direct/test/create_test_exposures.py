import numpy as np
import geopandas as gpd
import pycountry
from climada.entity.exposures.base import Exposures

# Create simple hazard objects for testing
# Adapted from the CLIMADA testing suite (originally called good_exposures)

test_country = 'Maldives'   # Not actually: just need a real name if this reaches the supply chain module
test_country_iso3alpha = pycountry.countries.get(name=test_country).alpha_3
test_country_iso3num = pycountry.countries.get(name=test_country).numeric

def test_exposures():
    """Followng values are defined for each exposure"""
    data = {}
    data['latitude'] = np.array([1, 2, 3])
    data['longitude'] = np.array([2, 3, 4])
    data['value'] = np.array([100, 100, 100])
    # data['deductible'] = np.array([1, 2, 3])
    data['impf_'] = np.array([1, 1, 1])
    # data['category_id'] = np.array([1, 2, 3])
    data['region_id'] = np.array([test_country_iso3alpha, test_country_iso3alpha, test_country_iso3alpha])
    data['country'] = np.array([test_country, test_country, test_country])
    data['iso3alpha'] = np.array([test_country_iso3num, test_country_iso3num, test_country_iso3num])
    # data['centr_TC'] = np.array([1, 2, 3])

    exp = Exposures(gpd.GeoDataFrame(data=data))
    return exp
