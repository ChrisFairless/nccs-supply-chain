"""
This file contains the full run of the pipeline. Some combinations are currently commented out, because they are not
either not yet fully developed (windstorms) or has not yet been decided which combinations are relevant
"""

import pathos as pa
ncpus = 3
ncpus = pa.helpers.cpu_count() - 1

#TODO add also other subsector to the configuration list
CONFIG = {
    "run_title": "refin_exposures_uncal_12_04_2024",
    "n_sim_years": 100,                     # Number of stochastic years of supply chain impacts to simulate
    "io_approach": ["leontief", "ghosh"],   # Supply chain IO to use. One or more of "leontief", "ghosh".
    "seed": 161,

    # Which parts of the model chain to run:
    "do_direct": True,                  # Calculate direct impacts (that aren't already calculated)
    "do_yearsets": True,                # Calculate direct impact yearsets (that aren't already calculated)
    "do_multihazard": False,            # Also combine hazards to create multi-hazard supply chain shocks
    "do_indirect": True,                # Calculate any indirect supply chain impacts (that aren't already calculated)

    # Impact functions:
    "business_interruption": True,      # Turn off to assume % asset loss = % production loss. Mostly for debugging and reproducibility
    "calibrated": True,                 # Turn off to use best guesstimate impact functions. Mostly for debugging and reproducibility

    # Parallisation:
    "do_parallel": True,                # Parallelise some operations
    "ncpus": ncpus,

    # Run specifications:
    "runs": [
        {
            "hazard": "tropical_cyclone",
            "sectors": ["agriculture", "forestry", "mining", "manufacturing", "service", "energy", "water", "waste",
                        "basic_metals", "pharmaceutical", "food", "wood", "chemical", "rubber_and_plastic",
                        "non_metallic_mineral", "refin_and_transform"],
            "countries": ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda', 'Argentina',
                          'Armenia', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh',
                          'Barbados',
                          'Belarus', 'Belgium', 'Belize', 'Benin', 'Bhutan', 'Bolivia, Plurinational State of',
                          'Bosnia and Herzegovina', 'Botswana', 'Brazil', 'Brunei Darussalam', 'Bulgaria',
                          'Burkina Faso',
                          'Burundi', 'Cabo Verde', 'Cambodia', 'Cameroon',
                          'Canada', 'Central African Republic', 'Chad', 'Chile', 'China', 'Colombia', 'Comoros',
                          'Congo',
                          'Congo, The Democratic Republic of the', 'Costa Rica', 'Croatia', "Côte d'Ivoire",
                          'Cuba', 'Cyprus', 'Czechia', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic',
                          'Timor-Leste', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea',
                          'Estonia', 'Eswatini', 'Ethiopia', 'Fiji', 'Finland', 'France', 'Gabon', 'Gambia', 'Georgia',
                          'Germany', 'Ghana', 'Greece', 'Grenada', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana',
                          'Haiti',
                          'Honduras', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran, Islamic Republic of', 'Iraq',
                          'Ireland', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati',
                          "Korea, Democratic People's Republic of",
                          'Korea, Republic of', 'Kuwait', 'Kyrgyzstan', "Lao People's Democratic Republic", 'Latvia',
                          'Lebanon',
                          'Lesotho', 'Liberia',
                          'Libya', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Madagascar', 'Malawi', 'Malaysia',
                          'Maldives',
                          'Mali', 'Malta', 'Marshall Islands', 'Mauritania', 'Mauritius',
                          'Mexico', 'Micronesia, Federated States of', 'Moldova, Republic of', 'Monaco', 'Mongolia',
                          'Morocco', 'Mozambique', 'Myanmar', 'Namibia', 'Nauru', 'Nepal', 'Netherlands',
                          'New Zealand', 'Nicaragua', 'Niger', 'Nigeria', 'North Macedonia', 'Norway', 'Oman',
                          'Pakistan',
                          'Palau', 'Panama', 'Papua New Guinea', 'Paraguay', 'Peru', 'Philippines', 'Poland',
                          'Portugal',
                          'Qatar', 'Romania', 'Russian Federation', 'Rwanda', 'Saint Kitts and Nevis', 'Saint Lucia',
                          'Saint Vincent and the Grenadines', 'Samoa', 'San Marino', 'Sao Tome and Principe',
                          'Saudi Arabia',
                          'Senegal', 'Seychelles', 'Sierra Leone', 'Singapore', 'Slovakia', 'Slovenia',
                          'Solomon Islands', 'Somalia', 'South Africa', 'Spain', 'Sri Lanka', 'Sudan',
                          'Suriname', 'Sweden', 'Syrian Arab Republic', 'Taiwan, Province of China',
                          'Tajikistan', 'Tanzania, United Republic of', 'Thailand',
                          'Togo', 'Tonga', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu',
                          'Uganda',
                          'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'Uzbekistan',
                          'Vanuatu', 'Venezuela, Bolivarian Republic of', 'Viet Nam', 'Yemen', 'Zambia',
                          'Zimbabwe'],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
                # {"scenario": "rcp26", "ref_year": "2040"},
                {"scenario": "rcp26", "ref_year": "2060"},
                # {"scenario": "rcp26", "ref_year": "2080"},
                # {"scenario": "rcp45", "ref_year": "2040"},
                # {"scenario": "rcp45", "ref_year": "2060"},
                # {"scenario": "rcp45", "ref_year": "2080"},
                # {"scenario": "rcp60", "ref_year": "2040"},
                # {"scenario": "rcp60", "ref_year": "2060"},
                # {"scenario": "rcp60", "ref_year": "2080"},
                # {"scenario": "rcp85", "ref_year": "2040"},
                {"scenario": "rcp85", "ref_year": "2060"},
            ]
        },
        {
            "hazard": "river_flood",
            "sectors": ["agriculture", "forestry", "mining", "manufacturing", "service", "energy", "water", "waste",
                        "basic_metals", "pharmaceutical", "food", "wood", "chemical", "rubber_and_plastic",
                        "non_metallic_mineral", "refin_and_transform"],
            "countries": ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda', 'Argentina',
                          'Armenia', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh',
                          'Barbados',
                          'Belarus', 'Belgium', 'Belize', 'Benin', 'Bhutan', 'Bolivia, Plurinational State of',
                          'Bosnia and Herzegovina', 'Botswana', 'Brazil', 'Brunei Darussalam', 'Bulgaria',
                          'Burkina Faso',
                          'Burundi', 'Cabo Verde', 'Cambodia', 'Cameroon',
                          'Canada', 'Central African Republic', 'Chad', 'Chile', 'China', 'Colombia', 'Comoros',
                          'Congo',
                          'Congo, The Democratic Republic of the', 'Costa Rica', 'Croatia', "Côte d'Ivoire",
                          'Cuba', 'Cyprus', 'Czechia', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic',
                          'Timor-Leste', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea',
                          'Estonia', 'Eswatini', 'Ethiopia', 'Fiji', 'Finland', 'France', 'Gabon', 'Gambia', 'Georgia',
                          'Germany', 'Ghana', 'Greece', 'Grenada', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana',
                          'Haiti',
                          'Honduras', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran, Islamic Republic of', 'Iraq',
                          'Ireland', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati',
                          "Korea, Democratic People's Republic of",
                          'Korea, Republic of', 'Kuwait', 'Kyrgyzstan', "Lao People's Democratic Republic", 'Latvia',
                          'Lebanon',
                          'Lesotho', 'Liberia',
                          'Libya', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Madagascar', 'Malawi', 'Malaysia',
                          'Maldives',
                          'Mali', 'Malta', 'Marshall Islands', 'Mauritania', 'Mauritius',
                          'Mexico', 'Micronesia, Federated States of', 'Moldova, Republic of', 'Monaco', 'Mongolia',
                          'Morocco', 'Mozambique', 'Myanmar', 'Namibia', 'Nauru', 'Nepal', 'Netherlands',
                          'New Zealand', 'Nicaragua', 'Niger', 'Nigeria', 'North Macedonia', 'Norway', 'Oman',
                          'Pakistan',
                          'Palau', 'Panama', 'Papua New Guinea', 'Paraguay', 'Peru', 'Philippines', 'Poland',
                          'Portugal',
                          'Qatar', 'Romania', 'Russian Federation', 'Rwanda', 'Saint Kitts and Nevis', 'Saint Lucia',
                          'Saint Vincent and the Grenadines', 'Samoa', 'San Marino', 'Sao Tome and Principe',
                          'Saudi Arabia',
                          'Senegal', 'Seychelles', 'Sierra Leone', 'Singapore', 'Slovakia', 'Slovenia',
                          'Solomon Islands', 'Somalia', 'South Africa', 'Spain', 'Sri Lanka', 'Sudan',
                          'Suriname', 'Sweden', 'Syrian Arab Republic', 'Taiwan, Province of China',
                          'Tajikistan', 'Tanzania, United Republic of', 'Thailand',
                          'Togo', 'Tonga', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu',
                          'Uganda',
                          'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'Uzbekistan',
                          'Vanuatu', 'Venezuela, Bolivarian Republic of', 'Viet Nam', 'Yemen', 'Zambia',
                          'Zimbabwe'],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
                # {"scenario": "rcp26", "ref_year": 2020},
                # {"scenario": "rcp26", "ref_year": 2040},
                {"scenario": "rcp26", "ref_year": 2060},
                # {"scenario": "rcp26", "ref_year": 2080},
                # {"scenario": "rcp60", "ref_year": 2020},
                # {"scenario": "rcp60", "ref_year": 2040},
                # {"scenario": "rcp60", "ref_year": 2060},
                # {"scenario": "rcp60", "ref_year": 2080},
                # {"scenario": "rcp85", "ref_year": 2020},
                # {"scenario": "rcp85", "ref_year": 2040},
                {"scenario": "rcp85", "ref_year": 2060},
                # {"scenario": "rcp85", "ref_year": 2080},
            ]
        },
        {
            "hazard": "wildfire",
            "sectors": ["agriculture", "forestry", "mining", "manufacturing", "service", "energy", "water", "waste",
                        "basic_metals", "pharmaceutical", "food", "wood", "chemical", "rubber_and_plastic",
                        "non_metallic_mineral", "refin_and_transform"],
            "countries": ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda', 'Argentina',
                          'Armenia', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh',
                          'Barbados',
                          'Belarus', 'Belgium', 'Belize', 'Benin', 'Bhutan', 'Bolivia, Plurinational State of',
                          'Bosnia and Herzegovina', 'Botswana', 'Brazil', 'Brunei Darussalam', 'Bulgaria',
                          'Burkina Faso',
                          'Burundi', 'Cabo Verde', 'Cambodia', 'Cameroon',
                          'Canada', 'Central African Republic', 'Chad', 'Chile', 'China', 'Colombia', 'Comoros',
                          'Congo',
                          'Congo, The Democratic Republic of the', 'Costa Rica', 'Croatia', "Côte d'Ivoire",
                          'Cuba', 'Cyprus', 'Czechia', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic',
                          'Timor-Leste', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea',
                          'Estonia', 'Eswatini', 'Ethiopia', 'Fiji', 'Finland', 'France', 'Gabon', 'Gambia', 'Georgia',
                          'Germany', 'Ghana', 'Greece', 'Grenada', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana',
                          'Haiti',
                          'Honduras', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran, Islamic Republic of', 'Iraq',
                          'Ireland', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati',
                          "Korea, Democratic People's Republic of",
                          'Korea, Republic of', 'Kuwait', 'Kyrgyzstan', "Lao People's Democratic Republic", 'Latvia',
                          'Lebanon',
                          'Lesotho', 'Liberia',
                          'Libya', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Madagascar', 'Malawi', 'Malaysia',
                          'Maldives',
                          'Mali', 'Malta', 'Marshall Islands', 'Mauritania', 'Mauritius',
                          'Mexico', 'Micronesia, Federated States of', 'Moldova, Republic of', 'Monaco', 'Mongolia',
                          'Morocco', 'Mozambique', 'Myanmar', 'Namibia', 'Nauru', 'Nepal', 'Netherlands',
                          'New Zealand', 'Nicaragua', 'Niger', 'Nigeria', 'North Macedonia', 'Norway', 'Oman',
                          'Pakistan',
                          'Palau', 'Panama', 'Papua New Guinea', 'Paraguay', 'Peru', 'Philippines', 'Poland',
                          'Portugal',
                          'Qatar', 'Romania', 'Russian Federation', 'Rwanda', 'Saint Kitts and Nevis', 'Saint Lucia',
                          'Saint Vincent and the Grenadines', 'Samoa', 'San Marino', 'Sao Tome and Principe',
                          'Saudi Arabia',
                          'Senegal', 'Seychelles', 'Sierra Leone', 'Singapore', 'Slovakia', 'Slovenia',
                          'Solomon Islands', 'Somalia', 'South Africa', 'Spain', 'Sri Lanka', 'Sudan',
                          'Suriname', 'Sweden', 'Syrian Arab Republic', 'Taiwan, Province of China',
                          'Tajikistan', 'Tanzania, United Republic of', 'Thailand',
                          'Togo', 'Tonga', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu',
                          'Uganda',
                          'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'Uzbekistan',
                          'Vanuatu', 'Venezuela, Bolivarian Republic of', 'Viet Nam', 'Yemen', 'Zambia',
                          'Zimbabwe'],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
            ]
        },
        {
            "hazard": "storm_europe",
            "sectors": ["agriculture", "forestry", "mining", "manufacturing", "service", "energy", "water", "waste",
                        "basic_metals", "pharmaceutical", "food", "wood", "chemical", "rubber_and_plastic",
                        "non_metallic_mineral", "refin_and_transform"],
            "countries": ['Albania', 'Algeria', 'Andorra',
                          'Austria', 'Belarus', 'Belgium', 'Bosnia and Herzegovina', 'Bulgaria', 'Croatia',
                          'Cyprus', 'Czechia', 'Denmark','Egypt', 'Estonia', 'Finland', 'France',
                          'Germany', 'Greece', 'Hungary', 'Iceland',
                          'Ireland', 'Italy', 'Latvia', 'Libya', 'Liechtenstein', 'Lithuania', 'Luxembourg',
                          'Moldova, Republic of', 'Monaco','Morocco', 'Netherlands', 'North Macedonia', 'Norway',
                          'Poland', 'Portugal','Romania', 'Slovakia', 'Slovenia', 'Spain', 'Sweden', 'Tunisia', 'Turkey',
                          'Ukraine', 'United Kingdom'],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
                # These combinations are possible, but since the windstorm is not yet developed fully, we exclude them.
                {"scenario": "rcp26", "ref_year": "future"},
                # {"scenario": "ssp245", "ref_year": "present"},
                # {"scenario": "ssp370", "ref_year": "present"},
                {"scenario": "rcp85", "ref_year": "future"},
            ]
        },

        {
            "hazard": "relative_crop_yield",
            "sectors": ["agriculture"],
            "countries": ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda', 'Argentina',
                          'Armenia', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh',
                          'Barbados',
                          'Belarus', 'Belgium', 'Belize', 'Benin', 'Bhutan', 'Bolivia, Plurinational State of',
                          'Bosnia and Herzegovina', 'Botswana', 'Brazil', 'Brunei Darussalam', 'Bulgaria',
                          'Burkina Faso',
                          'Burundi', 'Cabo Verde', 'Cambodia', 'Cameroon',
                          'Canada', 'Central African Republic', 'Chad', 'Chile', 'China', 'Colombia', 'Comoros',
                          'Congo',
                          'Congo, The Democratic Republic of the', 'Costa Rica', 'Croatia', "Côte d'Ivoire",
                          'Cuba', 'Cyprus', 'Czechia', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic',
                          'Timor-Leste', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea',
                          'Estonia', 'Eswatini', 'Ethiopia', 'Fiji', 'Finland', 'France', 'Gabon', 'Gambia', 'Georgia',
                          'Germany', 'Ghana', 'Greece', 'Grenada', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana',
                          'Haiti',
                          'Honduras', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran, Islamic Republic of', 'Iraq',
                          'Ireland', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati',
                          "Korea, Democratic People's Republic of",
                          'Korea, Republic of', 'Kuwait', 'Kyrgyzstan', "Lao People's Democratic Republic", 'Latvia',
                          'Lebanon',
                          'Lesotho', 'Liberia',
                          'Libya', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Madagascar', 'Malawi', 'Malaysia',
                          'Maldives',
                          'Mali', 'Malta', 'Marshall Islands', 'Mauritania', 'Mauritius',
                          'Mexico', 'Micronesia, Federated States of', 'Moldova, Republic of', 'Monaco', 'Mongolia',
                          'Morocco', 'Mozambique', 'Myanmar', 'Namibia', 'Nauru', 'Nepal', 'Netherlands',
                          'New Zealand', 'Nicaragua', 'Niger', 'Nigeria', 'North Macedonia', 'Norway', 'Oman',
                          'Pakistan',
                          'Palau', 'Panama', 'Papua New Guinea', 'Paraguay', 'Peru', 'Philippines', 'Poland',
                          'Portugal',
                          'Qatar', 'Romania', 'Russian Federation', 'Rwanda', 'Saint Kitts and Nevis', 'Saint Lucia',
                          'Saint Vincent and the Grenadines', 'Samoa', 'San Marino', 'Sao Tome and Principe',
                          'Saudi Arabia',
                          'Senegal', 'Seychelles', 'Sierra Leone', 'Singapore', 'Slovakia', 'Slovenia',
                          'Solomon Islands', 'Somalia', 'South Africa', 'Spain', 'Sri Lanka', 'Sudan',
                          'Suriname', 'Sweden', 'Syrian Arab Republic', 'Taiwan, Province of China',
                          'Tajikistan', 'Tanzania, United Republic of', 'Thailand',
                          'Togo', 'Tonga', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu',
                          'Uganda',
                          'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'Uzbekistan',
                          'Vanuatu', 'Venezuela, Bolivarian Republic of', 'Viet Nam', 'Yemen', 'Zambia',
                          'Zimbabwe'],
            "scenario_years": [
                {"scenario": "None", "ref_year": "historical"},
                {"scenario": "rcp60", "ref_year": "future"},
            ]
        }
    ]
}