"""
This file contains the full run of the pipeline. Some combinations are currently commented out, because they are not
either not yet fully developed (windstorms) or has not yet been decided which combinations are relevant
"""

CONFIG = {
    "run_title": "best_guesstimate_17_01_2024",
    "io_approach": "ghosh",
    "n_sim_years": 100,
    "runs": [
        {
            "hazard": "tropical_cyclone",
            "sectors": ["mining", "manufacturing", "service", "electricity", "agriculture","forestry"],
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
                # {"scenario": "rcp26", "ref_year": "2040"}, #have the run for this for some countries
                {"scenario": "rcp26", "ref_year": "2060"},  # TODO @mastaia run this
                # {"scenario": "rcp26", "ref_year": "2080"},
                # {"scenario": "rcp45", "ref_year": "2040"},
                # {"scenario": "rcp45", "ref_year": "2060"},
                # {"scenario": "rcp45", "ref_year": "2080"},
                # {"scenario": "rcp60", "ref_year": "2040"},
                # {"scenario": "rcp60", "ref_year": "2060"},#have the run for this one
                # {"scenario": "rcp60", "ref_year": "2080"},
                # {"scenario": "rcp85", "ref_year": "2040"},
                {"scenario": "rcp85", "ref_year": "2060"},  # have the run for this for some countries
            ]
        },
        {
            "hazard": "river_flood",
            "sectors": ["mining", "manufacturing", "service", "electricity", "agriculture","forestry"],
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
                # {"scenario": "rcp26", "ref_year": 2040}, #have the run for this
                {"scenario": "rcp26", "ref_year": 2060},  # TODO @mastaia run this code
                # {"scenario": "rcp26", "ref_year": 2080},
                # {"scenario": "rcp60", "ref_year": 2020},
                # {"scenario": "rcp60", "ref_year": 2040},
                # {"scenario": "rcp60", "ref_year": 2060}, #have the run for this
                # {"scenario": "rcp60", "ref_year": 2080},
                # {"scenario": "rcp85", "ref_year": 2020},
                # {"scenario": "rcp85", "ref_year": 2040},
                {"scenario": "rcp85", "ref_year": 2060},  # have the run for this
                # {"scenario": "rcp85", "ref_year": 2080},
            ]
        },
        {
            "hazard": "wildfire",
            "sectors": ["mining", "manufacturing", "service", "electricity", "agriculture","forestry"],
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
            "sectors": ["mining", "manufacturing", "service", "electricity", "agriculture","forestry"],
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
                {"scenario": "None", "ref_year": "present"},
                # These combinations are possible, but since the windstorm is not yet developed fully, we exclude them.
                # {"scenario": "ssp126", "ref_year": "present"}, #TODO run this
                # {"scenario": "ssp245", "ref_year": "present"},
                # {"scenario": "ssp370", "ref_year": "present"},
                # {"scenario": "ssp585", "ref_year": "present"}, #TODO run this
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
                {"scenario": "rcp60", "ref_year": "2006_2099"},
            ]
        }
    ]
}
