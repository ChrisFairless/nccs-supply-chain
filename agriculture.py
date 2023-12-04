import typing

from climada.entity import ImpactFuncSet
from climada.util.api_client import Client
from climada_petals.entity.impact_funcs.relative_cropyield import ImpfRelativeCropyield
from pycountry import countries

CropType = typing.Literal[
    "whe",
    "mai",
    "soy",
    "ric",
]
IrrigationType = typing.Literal["firr", "noirr"]


def get_exposure(crop_type: CropType = "whe", scenario="histsoc", irr: IrrigationType = "firr"):
    client = Client()
    return client.get_exposures(
        "crop_production", properties={
            "irrigation_status": irr,
            "crop": crop_type,
            "unit": "USD"
        }
    )


def get_impf_set():
    impf_cp = ImpactFuncSet()
    impf_def = ImpfRelativeCropyield()
    impf_def.set_relativeyield()
    impf_cp.append(impf_def)
    impf_cp.check()
    return impf_cp


def get_hazard(country,
               year_range,
               scenario: typing.Literal["historical", "rcp60"] = "historical",
               crop_type: CropType = "whe",
               irr: IrrigationType = "firr"):
    # TODO how to filter the hazard by country?
    # TODO how to map the year to the years in this model
    # TODO What about the firr and noirr?
    print(country, year_range, scenario, crop_type, irr)
    client = Client()
    hazard = client.get_hazard(
        "relative_cropyield",
        properties={
            'climate_scenario': scenario,
            'crop': crop_type,
            'irrigation_status': irr
        }
    )
    hazard.centroids.set_region_id()
    region_id = int(countries.get(alpha_3=country).numeric)
    return hazard.select(reg_id=region_id)
