import numpy as np
from scipy import sparse
import datetime as dt

from climada.engine import Impact
from climada.util.constants import DEF_CRS

# Create simple impact objects for testing
# Copied from climada.engine.test.test_impact

def dummy_impact():
    """Return an impact object for testing"""
    return Impact(
        event_id=np.arange(6) + 10,
        event_name=[0, 1, "two", "three", 30, 31],
        date=np.arange(6),
        coord_exp=np.array([[1, 2], [1.5, 2.5]]),
        crs=DEF_CRS,
        eai_exp=np.array([7.2, 7.2]),
        at_event=np.array([0, 2, 4, 6, 60, 62]),
        frequency=np.array([1 / 6, 1 / 6, 1, 1, 1 / 30, 1 / 30]),
        tot_value=7,
        aai_agg=14.4,
        unit="USD",
        frequency_unit="1/month",
        imp_mat=sparse.csr_matrix(
            np.array([[0, 0], [1, 1], [2, 2], [3, 3], [30, 30], [31, 31]])
        ),
        haz_type="TC",
    )

def dummy_impact_yearly():
    """Return an impact containing events in multiple years"""
    imp = dummy_impact()

    years = np.arange(2010,2010+len(imp.date))

    # Edit the date and frequency
    imp.date = np.array([dt.date(year,1,1).toordinal() for year in years])
    imp.frequency_unit = "1/year"
    imp.frequency = np.ones(len(years))/len(years)

    # Calculate the correct expected annual impact
    freq_mat = imp.frequency.reshape(len(imp.frequency), 1)
    imp.eai_exp = imp.imp_mat.multiply(freq_mat).sum(axis=0).A1
    imp.aai_agg = imp.eai_exp.sum()

    return imp