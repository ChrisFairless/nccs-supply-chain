from climada.entity import ImpactFunc, ImpactFuncSet, ImpfTropCyclone

def test_impf():
    impf = ImpactFunc(
        haz_type='TC',
        id=1,
        intensity = [0, 1],
        mdd = [0, 1],
        paa = [1, 1],
        name='test_impact_func'
    )
    return impf

def test_impfset():
    return ImpactFuncSet([test_impf()])