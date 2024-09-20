from setuptools import setup, find_namespace_packages

setup(name='nccs',
    version='0.1',
    description='NCCS Supply Chain module',
    url='http://github.com/ChrisFairless/nccs-supply-chain',
    author=['Chris Fairless', 'Alina Mastai', 'Gaudenz Halter', 'Samuel Juhel', 'Michael Gloor', 'Kaspar Tobler'],
    author_email='chrisfairless@hotmail.com',
    license='OSI Approved :: GNU Lesser General Public License v3 (GPLv3)',
    python_requires=">=3.9,<3.12",
    install_requires=[
        'bokeh',
        'boto3',
        'python-dotenv',
        'climada'
    ],
    dependency_links=['https://github.com/CLIMADA-project/climada_petals.git@v5.0.0'],
    packages=find_namespace_packages(include=['climada*']),
    include_package_data=True
)
