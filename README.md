# Installation

This will set up this repository with Anaconda virtual environment.

On the command line, create a new environment (here called nccs, you can choose any name):

```
conda env create -n nccs
```

Then activate the environment and install the requirements:
```
conda activate nccs
pip install -r requirements.txt
```

If the installation fails you may need to update pip:
```
pip3 install --upgrade pip
```

Note: this isn't a perfectly specified environment. CLIMADA and CLIMADA petals have such a complex set of dependencies that solving the Conda environment takes hours. Since CLIMADA Core, CLIMADA Petals and the NCCS dependencies will be updated as the project goes along, the requirements.txt file should be enough to run the code here for now.