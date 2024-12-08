"""
This file contains the full run of the pipeline.
"""
import pathos as pa
ncpus = 3
ncpus = pa.helpers.cpu_count() - 1


CONFIG = {
    "run_title": "mvp_sea_level",
    "n_sim_years": 300,                     # Number of stochastic years of supply chain impacts to simulate
    "io_approach": ["ghosh", "leontief"],   # Supply chain IO to use. One or more of "leontief", "ghosh"
    "force_recalculation": False,           # If an intermediate file or output already exists should it be recalculated?
    "use_s3": False,                        # Also load and save data from an S3 bucket
    "log_level": "INFO",
    "seed": 161,

    # Which parts of the model chain to run:
    "do_direct": True,                      # Calculate direct impacts (that aren't already calculated)
    "do_yearsets": True,                    # Calculate direct impact yearsets (that aren't already calculated)
    "do_multihazard": False,                # Also combine hazards to create multi-hazard supply chain shocks
    "do_indirect": True,                    # Calculate any indirect supply chain impacts (that aren't already calculated)
    "use_sector_bi_scaling": True,           # Calculate sectoral business interruption scaling

    # Impact functions:
    "business_interruption": True,          # Turn off to assume % asset loss = % production loss. Mostly for debugging and reproducibility
    "calibrated": True,                     # Turn off to use best guesstimate impact functions. Mostly for debugging and reproducibility

    # Parallisation:
    "do_parallel": False,  # Parallelise some operations
    "ncpus": ncpus,

    "runs": [
        {
            "hazard": "sea_level_rise",
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
                          'Haiti', 'Honduras', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran, Islamic Republic of', 'Iraq',
                          'Ireland', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati',
                          "Korea, Democratic People's Republic of",
                          'Korea, Republic of', 'Kuwait', 'Kyrgyzstan', "Lao People's Democratic Republic", 'Latvia',
                          'Lebanon', 'Lesotho', 'Liberia',
                          'Libya', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Madagascar', 'Malawi', 'Malaysia',
                          'Maldives', 'Mali', 'Malta', 'Marshall Islands', 'Mauritania', 'Mauritius',
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
                {"scenario": "ssp126", "ref_year": 2060},
                {"scenario": "ssp585", "ref_year": 2060},

            ]
        }
    ]
}