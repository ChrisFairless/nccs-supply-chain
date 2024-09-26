from climada.entity import ImpactFuncSet, ImpfTropCyclone

def test_impf():
    impf = ImpfTropCyclone.from_emanuel_usa(
                scale=1,
                v_thresh=0,
                v_half=0.5
    )
    impf.id = 1
    impf.haz_type = 'TC'
    return impf

def test_impfset():
    return ImpactFuncSet(test_impf())