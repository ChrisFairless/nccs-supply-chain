import numpy as np
from scipy import sparse
from climada.hazard import Hazard, Centroids

# Create simple hazard objects for testing
# Copied from the CLIMADA testing suite

def test_hazard():
    fraction = sparse.csr_matrix([[0.1, 0.1, 0.1],
                                  [1, 1, 1],
                                  [1, 1, 1],
                                  [1, 1, 1]])
    intensity = sparse.csr_matrix([[1, 1, 1],
                                   [0.0, 0.0, 0.0],
                                   [0.5, 0.5, 0.5],
                                   [1, 1, 1]])

    return Hazard(
        "TC",
        intensity=intensity,
        fraction=fraction,
        centroids=Centroids.from_lat_lon(
            np.array([1, 2, 3]), np.array([2.001, 3.001, 4.001])),  # almost match the test exposure
        event_id=np.array([1, 2, 3, 4]),
        event_name=['ev1', 'ev2', 'ev3', 'ev4'],
        date=np.array([1, 2, 3, 4]),
        orig=np.array([True, False, False, True]),
        frequency=np.array([0.1, 0.5, 0.5, 0.2]),
        frequency_unit='1/week',
        units='m/s',
    )

