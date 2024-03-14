import requests
import os

def download_tif_files(links_file, output_folder):
    with open(links_file, 'r') as file:
        for line in file:
            url = line.strip()
            filename = url.split('/')[-1]
            output_path = os.path.join(output_folder, filename)
            print("Downloading", filename)
            response = requests.get(url)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print("Downloaded", filename)


links_file = 'data/deforestation/lossyear.txt'  # Path to your text file containing the links
output_folder = 'data/deforestation'  # Folder where you want to save the downloaded files

download_tif_files(links_file, output_folder)





