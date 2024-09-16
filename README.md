# Installation

This will set up this repository with the Mamba virtual environment.

Why Mamba and not Anaconda? CLIMADA and CLIMADA Petals have such a complex set of dependencies that solving the Conda environment takes hours.

## Prerequisites

(Copied from the [CLIMADA install instructions](https://climada-python.readthedocs.io/en/stable/guide/install.html): )

- Make sure you are using the latest version of your OS. Install any outstanding updates.
- Install git as a command line tool.
- Free up at least 10 GB of free storage space on your machine. Mamba and the CLIMADA dependencies will require around 5 GB of free space, and you will need at least that much additional space for storing the input and output data of CLIMADA.
- Ensure a stable internet connection for the installation procedure. All dependencies will be downloaded from the internet. Do not use a metered, mobile connection!
- Install the Conda environment management system. We highly recommend you use [Miniforge](https://github.com/conda-forge/miniforge), which includes the potent [Mamba](https://mamba.readthedocs.io/en/latest/) package manager. Download the installer suitable for your system and follow the respective installation instructions. (See also [Conda as Alternative to Mamba](https://climada-python.readthedocs.io/en/stable/guide/install.html#conda-instead-of-mamba)).

## Simple instructions

These will install a stable(ish) version of the repository. If you're not planning to make any changes to the underlying CLIMADA Core or Petals codebases, this is the way to install.

1. Clone this repository to your local machine. To do this to your current directory from the command line:

```
git clone https://github.com/ChrisFairless/nccs-supply-chain
```

2. Navigate to the repository and create a new Conda environment. 
```
cd nccs-supply-chain
mamba create --name nccs python=3.9
```
Notes:
- Python 3.9 is required for the version of CLIMADA we will install
- Mamba has trouble creating environments from yml files so we add packages in the next step

3. Install the requirements into the environment:
```
mamba env update -n nccs -f requirements/requirements.yml
```
Notes:
- Parts of the NCCS codebase rely on raster functionality that was removed from CLIMADA Core in a recent update. We haven't yet updated the code to handle this. Version 4.1.0 of CLIMADA is therefore installed by the requirements file.
- The CLIMADA Petals Supply Chain module is frequently updated, so here we install the latest version of it (June 2024). In the future we will want to pin this version.

4. Activate the environment
```
mamba activate nccs
```
Notes:
- Some systems with Conda already installed won't recognise mamba-created environments. If this happens run `conda info --envs` to see the directories where conda and mamba environments are stored, and then run `conda activate <path_to_environment>` to activate it.

5. (Optional) Check the installation was a success. From the nccs-supply-chain directory you can execute unit tests. These include a short end-to-end run of the NCCS pipeline. Note that this will download several files and create results directories. If this is your first time using CLIMADA it's possible this could take some time. Run these with
```
python -m unittest
```


## Add Jupyter functionality

If you're planning to run Jupyter notebooks while working in this environment, you can extend the environment with
```
mamba env update -n nccs -file requirements/requirements_jupyter.yml
```


## Install a development environment

If you want to install the repository in a way that lets you make modifications to the underlying CLIMADA Core and Petals code and run analyses with the updated packages, you need copies of both CLIMADA Core and Petals on your local machine with an interactive installation via pip:

1. Download this repository, [CLIMADA](https://climada-python.readthedocs.io/) and [CLIMADA Petals](https://climada-petals.readthedocs.io/) if you don't have them already:
```
git clone https://github.com/ChrisFairless/nccs-supply-chain
git clone https://github.com/CLIMADA-project/climada_python
git clone https://github.com/CLIMADA-project/climada_petals
```
Note the paths to the directories where they are stored. If you want to work on a different branch to `main`, check out the relevant branches.


2. On the command line, navigate to the nccs-supply-chain repository and create a new environment (here called nccs_dev, you can choose any name):

```
cd <path_to_nccs_repo>
mamba create -name nccs_dev python=3.9
```

3. Install CLIMADA Core's environment requirements:
```
mamba env update -n nccs_dev --file <path_to_climada_python_repo>/requirements/env_climada.yml
```
Notes:
- If the installation fails you may need to update pip with `pip3 install --upgrade pip`


4. Install CLIMADA Petal's environment requirements:
```
mamba env update -n nccs_dev --file <path_to_climada_petals_repo>/requirements/env_climada.yml
```

5. Activate your environment and install CLIMADA Core and Petals
```
mamba activate nccs_dev
python -m pip install -e <path_to_climada_python_repo>
python -m pip install -e <path_to_climada_petals_repo>
```
Notes:
- Some systems with Conda already installed won't recognise mamba-created environments. If this happens run `conda info --envs` to see the directories where conda and mamba environments are stored, and then run `conda activate <path_to_environment>` to activate it.

6. Finally install the NCCS dev environment requirements:
```
mamba env update -n nccs_dev --file requirements/requirements_dev.yml
```

You should now be ready to go. Any changes you make to your local copy of CLIMADA Core or Petals will automatically be updated in your installed versions of the packages when they are called by NCCS code.

7. (Optional) If you're planning to run Jupyter notebooks, install Jupyter following the instructions in the section above.

8. (Optional) Check the installation was a success. From the nccs-supply-chain directory you can execute unit tests. These include a short end-to-end run of the NCCS pipeline. Note that this will download several files and create results directories. If this is your first time using CLIMADA it's possible this could take some time. Run these with
```
python -m unittest
```

### A note on CLIMADA versions

Some parts of the NCCS repository rely on functionality from different 'periods' of CLIMADA's history.

The above instructions set up CLIMADA as it's required to run the modelling pipeline. This uses CLIMADA 5.0.0 or higher, which is required by the latest tropical cyclone event set (changed from 4.1.0 on 16 Sept 2024).

However, the code used to generate the European Windstorm data depends on version 4.1.0 or earlier. This is _not_ required to run the model pipeline, which uses precalculated windstorm data. It's only relevant if you want to (re)generate windstorm data. 

You can always change versions of CLIMADA (when you have the development environment set up as in these instructions) on the command line:
```
cd <path_to_climada_python_repo>
git checkout v4.1.0
cd <path_to_nccs_repo>
```
The above commands work at any time, before or after installation, since CLIMADA is installed interactively (see below).

Notes:
- We can't guarantee that changes between CLIMADA versions work 100% of the time, since different versions of CLIMADA have different package dependencies. If this happens, follow these installation instructions again, but check out the correct version of CLIMADA with the above command immediately after Step 1. This way the correct dependencies for that version of CLIMADA will be installed in Step 3.
