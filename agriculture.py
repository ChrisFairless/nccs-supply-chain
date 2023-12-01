import glob
import os
import pathlib
import typing

import requests
from climada.entity import ImpactFuncSet
from climada.util.constants import DEMO_DIR as INPUT_DIR
from climada_petals.entity.exposures.crop_production import CropProduction
from climada_petals.entity.impact_funcs.relative_cropyield import ImpfRelativeCropyield
from climada_petals.hazard.relative_cropyield import set_multiple_rc_from_isimip

EXPOSURE_FILE_OVERRIDE = None # r"C:\Users\GaudenzHalter\Downloads\histsoc_landuse-15crops_annual_1861_2018.nc4" I need this because of storage reasons....
_AGR_MODEL = None
CropType = typing.Literal[
    "whe",
    "mai",
    "soy",
    "ric",
]
IrrigationType = typing.Literal["firr", "noirr"]


class AgricultureModule:
    def __init__(self, input_dir, output_dir, exposure_file=None):
        self.input_dir = input_dir
        self._input_yield_dir = os.path.join(input_dir, "crop_yields")
        self._input_exp_dir = os.path.join(input_dir, "exposure")
        if exposure_file is None:
            exposure_file = os.path.join(self._input_exp_dir, "histsoc_landuse-15crops_annual_1861_2018.nc4")
        self._exposure_file = exposure_file
        self.output_dir = output_dir

        self.download_data()

    def download_data(self):
        with open(f"{self.input_dir}/filelist.txt", "r") as f:
            filelist = f.read().splitlines()
        for file in filelist:
            out_file = os.path.basename(file)
            out_file = f"{self._input_yield_dir}/{out_file}"
            os.makedirs(self._input_yield_dir, exist_ok=True)

            if os.path.exists(out_file):
                print(f"File {out_file} already exists, skipping download.")
                continue

            with open(out_file, "wb") as f:
                print(f"Downloading {file}...")
                res = requests.get(file)
                f.write(res.content)

        if not os.path.isfile(self._exposure_file):
            with open(f"{self.input_dir}/filelist_exposure.txt", "r") as f:
                filelist = f.read().splitlines()[0]

            out_file = os.path.basename(filelist)
            out_file = f"{self._input_exp_dir}/{out_file}"
            os.makedirs(self._input_exp_dir, exist_ok=True)

            with open(out_file, "wb") as f:
                print(f"Downloading {file}...")
                res = requests.get(file)
                f.write(res.content)

    def load_hazard(self):
        input_haz_dir = "agriculture/crop_yields"  # set path where you place hazard input data

        # (Place crop yield data (.nc) from ISIMIP in input_haz_dir)

        path_hist_mean = f"{self.output_dir}/hist_mean"  # set output directory for hist_mean
        os.makedirs(path_hist_mean, exist_ok=True)

        filelist_haz, hazards_list = set_multiple_rc_from_isimip(
            input_dir=input_haz_dir,
            output_dir=self.output_dir,
            isimip_run='ISIMIP2b',
            return_data=True
        )
        return hazards_list

    def load_exposure(self,
                      crop_type: CropType = "whe",
                      scenario="flexible",
                      irr: IrrigationType = "firr"):

        # This has been produced by load_hazard
        filename_mean = f"{self.output_dir}/hist_mean/hist_mean_{crop_type}-{irr}*"
        filename_mean = glob.glob(filename_mean)[0]
        exp = CropProduction()
        filename = pathlib.Path(self._exposure_file)
        filename_mean = pathlib.Path(filename_mean)
        exp.set_from_isimip_netcdf(
            input_dir=INPUT_DIR,
            filename=filename,
            hist_mean=filename_mean,
            # bbox=[-5, 42, 16, 55], # do we need this?
            yearrange=(2001, 2005),  # do we need this?
            crop=crop_type,
            scenario=scenario,
            unit='t/y',
            irr=irr
        )
        exp.set_value_to_usd(input_dir=self.input_dir)  # convert exposure from t/y to USD/y using FAO statistics
        return exp


def _get_model():
    global _AGR_MODEL
    if _AGR_MODEL is None:
        _AGR_MODEL = AgricultureModule(
            input_dir="agriculture",
            output_dir="agriculture",
            exposure_file=EXPOSURE_FILE_OVERRIDE
        )
    return _AGR_MODEL


def get_exposure(crop_type: CropType = "whe", scenario="histsoc", irr: IrrigationType = "firr"):
    model = _get_model()
    exp = model.load_exposure(
        crop_type=crop_type,
        scenario=scenario,
        irr=irr
    )
    return exp


def get_impf_set():
    impf_cp = ImpactFuncSet()
    impf_def = ImpfRelativeCropyield()
    impf_def.set_relativeyield()
    impf_cp.append(impf_def)
    impf_cp.check()
    return impf_cp


def get_hazard(country, year_range, scenario):
    # TODO how to filter the hazard by country?
    # TODO how to map the year to the years in this model
    # TODO What about the irr and noirr?

    model = _get_model()
    hazard = model.load_hazard()[0]
    return hazard
