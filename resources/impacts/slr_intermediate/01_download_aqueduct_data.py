import requests
import os
from pathlib import Path
import pandas as pd

aqueduct_url = 'https://wri-projects.s3.amazonaws.com/AqueductFloodTool/download/v2/'
output_directory = Path('.', 'data', 'raw')

rp_list = [1, 2, 5, 10, 25, 50, 100, 250, 500, 1000]

filename_base_list = [
    'inuncoast',
]
scenario_list = [
    'historical',
    'rcp4p5',
    'rcp8p5'
]
subsidence_list = [
    'wtsub',
]
year_list = [
    '2050',
    '2080'
]
perc_list = [
    None,
    50
]


def download_file(filename, base_url, outdir):
    print(filename)
    out_path = Path(outdir, filename)
    if os.path.exists(out_path):
        print('File already exists at this location. Skipping: ' + str(out_path))
        return out_path
    response = requests.get(base_url + filename)
    if response.ok:
        with open(out_path, mode="wb") as f:
            f.write(response.content)
    else:
        raise ValueError('Download failed')
    return out_path


download_list = []

for filename_base in filename_base_list:
    for scenario in scenario_list:
        for subsidence in subsidence_list:
            if scenario == 'historical':
                scenario_year_list = ['hist']
            else:
                scenario_year_list = year_list
            #TODO the same for percentiles, it'll simplify things
            for year in scenario_year_list:
                for rp in rp_list:
                    rp_decimal = '5' if rp == 1 else '0'
                    if scenario == 'historical':
                        filename = f'{filename_base}_{scenario}_{subsidence}_{year}_rp{rp:04d}_{rp_decimal}.tif'
                        out_path = download_file(filename, aqueduct_url, output_directory)
                        d = dict(
                            filename_base = filename_base,
                            scenario = scenario,
                            subsidence = subsidence,
                            year = year,
                            rp_int = rp,
                            rp_decimal = rp_decimal,
                            rp = float(rp) + float(rp_decimal) / 10,
                            perc = None,
                            url = aqueduct_url + filename,
                            local_path = str(out_path)
                        )
                        download_list = download_list + [d]
                    else:
                        for perc in perc_list:
                            if perc is None:
                                filename = f'{filename_base}_{scenario}_{subsidence}_{year}_rp{rp:04d}_{rp_decimal}.tif'
                            else:
                                filename = f'{filename_base}_{scenario}_{subsidence}_{year}_rp{rp:04d}_{rp_decimal}_perc_{str(perc)}.tif'
                            out_path = download_file(filename, aqueduct_url, output_directory)
                            d = dict(
                                filename_base = filename_base,
                                scenario = scenario,
                                subsidence = subsidence,
                                year = year,
                                rp_int = rp,
                                rp_decimal = rp_decimal,
                                rp = float(rp) + float(rp_decimal) / 10,
                                perc = 95 if not perc else perc,
                                url = aqueduct_url + filename,
                                local_path = str(out_path)
                            )
                            download_list = download_list + [d]


df = pd.DataFrame(download_list)
df.to_csv(Path('.', 'data', 'aqueduct_download_metadata.csv'))