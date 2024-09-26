mamba create --name nccs python=3.9
mamba env update -n nccs -f requirements/requirements.yml
mamba env update -n nccs -f requirements/requirements_jupyter.yml
