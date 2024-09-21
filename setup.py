from setuptools import setup, find_packages

setup(
    name='nccs',
    version='0.1',
    description='NCCS Supply Chain module',
    url='http://github.com/example',
    author='NCCS',
    author_email='chrisfairless@hotmail.com',
    license='OSI Approved :: GNU Lesser General Public License v3 (GPLv3)',
    python_requires=">=3.9,<3.12",
    install_requires=[
        'bokeh',
        'boto3',
        'python-dotenv',
        'climada',
        'climada_petals @ git+https://github.com/CLIMADA-project/climada_petals.git@v5.0.0'
    ],
    packages=find_packages(),
    include_package_data=True
)
