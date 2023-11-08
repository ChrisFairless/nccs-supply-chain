import os.path

from calc_yearset import nccs_yearsets_simple
# from utils.s3client import download_from_s3_bucket, upload_to_s3_bucket
from direct import get_sector_exposure, nccs_direct_impacts_list_simple
from indirect import dump_supchain_to_csv, supply_chain_climada

# original
# country_list = ['Saint Kitts and Nevis', 'Jamaica', "China", "United States"]
# hazard_list = ['tropical_cyclone', 'river_flood']
# sector_list = ['service', 'service']
# scenario = 'rcp60'
# ref_year = 2080
# n_sim_years = 100


country_list = ['Australia', 'Austria', 'Belgium', 'Bulgaria', 'Brazil', 'Canada', 'Croatia', 'China', 'Cyprus',
                'Czechia',
                'Denmark', 'Estonia', 'Finland', 'France', 'Germany',
                'Greece', 'Hungary', 'Indonesia', 'Ireland',
                'Italy', 'India', 'Japan', 'Korea, Republic of', 'Latvia', 'Libya', 'Lithuania', 'Luxembourg',
                'Malta', 'Mexico', 'Netherlands', 'Norway', 'Poland', 'Portugal', 'Puerto Rico',
                'Romania', 'Russian Federation', 'Slovakia', 'Slovenia', 'Spain', 'Sweden',
                'Switzerland', 'Taiwan, Province of China', 'Turkey', 'United Kingdom',
                'United States']

global_countries = ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda', 'Argentina',
                    'Armenia', 'Australia', 'Austria', 'Azerbaijan', 'The Bahamas', 'Bahrain', 'Bangladesh', 'Barbados',
                    'Belarus', 'Belgium', 'Belize', 'Benin', 'Bhutan', 'Bolivia', 'Bosnia and Herzegovina', 'Botswana',
                    'Brazil', 'Brunei', 'Bulgaria', 'Burkina Faso', 'Burundi', 'Cabo Verde', 'Cambodia', 'Cameroon',
                    'Canada', 'Central African Republic', 'Chad', 'Chile', 'China', 'Colombia', 'Comoros', 'Congo',
                    ' Democratic Republic of the', 'Congo, Republic of the', 'Costa Rica', 'Côte d’Ivoire', 'Croatia',
                    'Cuba', 'Cyprus', 'Czech Republic', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic',
                    'East Timor (Timor-Leste)', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea',
                    'Estonia', 'Eswatini', 'Ethiopia', 'Fiji', 'Finland', 'France', 'Gabon', 'The Gambia', 'Georgia',
                    'Germany', 'Ghana', 'Greece', 'Grenada', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana', 'Haiti',
                    'Honduras', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran', 'Iraq', 'Ireland', 'Israel',
                    'Italy', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati', 'Korea,North',
                    'Korea, South', 'Kosovo', 'Kuwait', 'Kyrgyzstan', 'Laos', 'Latvia', 'Lebanon', 'Lesotho', 'Liberia',
                    'Libya', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Madagascar', 'Malawi', 'Malaysia', 'Maldives',
                    'Mali', 'Malta', 'Marshall Islands', 'Mauritania', 'Mauritius',
                    'Mexico,''Micronesia, Federated States of', 'Moldova', 'Monaco', 'Mongolia', 'Montenegro',
                    'Morocco', 'Mozambique', 'Myanmar (Burma)', 'Namibia', 'Nauru', 'Nepal', 'Netherlands',
                    'New Zealand,', 'Nicaragua', 'Niger', 'Nigeria', 'North Macedonia', 'Norway', 'Oman', 'Pakistan',
                    'Palau', 'Panama', 'Papua New Guinea', 'Paraguay', 'Peru', 'Philippines', 'Poland', 'Portugal',
                    'Qatar', 'Romania', 'Russia', 'Rwanda', 'Saint Kitts and Nevis', 'Saint Lucia',
                    'Saint Vincent and the Grenadines', 'Samoa', 'San Marino', 'Sao Tome and Principe', 'Saudi Arabia',
                    'Senegal', 'Serbia', 'Seychelles', 'Sierra Leone', 'Singapore', 'Slovakia', 'Slovenia',
                    'Solomon Islands', 'Somalia', 'South Africa', 'Spain', 'Sri Lanka', 'Sudan', 'Sudan, South',
                    'Suriname', 'Sweden', 'Switzerland', 'Syria', 'Taiwan', 'Tajikistan', 'Tanzania', 'Thailand',
                    'Togo', 'Tonga', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu', 'Uganda',
                    'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay', 'Uzbekistan',
                    'Vanuatu', 'Vatican City''Venezuela', 'Vietnam', 'Yemen', 'Zambia', 'Zimbabwe']

hazard_list = ['river_flood']  # ['tropical_cyclone', 'river_flood']
sector_list = ['manufacturing']
# sector_list = ['manufacturing', 'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing',
#                'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing',
#                'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing',
#                'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing',
#                'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing',
#                'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing',
#                'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing'
#                'manufacturing', 'manufacturing', 'manufacturing', 'manufacturing']  # ['service', 'service']

scenario = 'rcp60'
ref_year = 2080
n_sim_years = 100


def calc_supply_chain_impacts(
        country_list,
        hazard_list,
        sector_list,
        scenario,
        ref_year,
        n_sim_years,
        save_by_country=False,
        save_by_hazard=False,
        save_by_sector=False,
        seed=1312
):
    ### --------------------------------- ###
    ### CALCULATE DIRECT ECONOMIC IMPACTS ###
    ### --------------------------------- ###

    # Generate a data frame with metadata, exposure objects and impact objects 
    # for each combination of input factors.
    analysis_df = nccs_direct_impacts_list_simple(hazard_list, sector_list, country_list, scenario, ref_year)

    ### ------------------- ###
    ### SAMPLE IMPACT YEARS ###
    ### ------------------- ###

    # Sample impact objects to create a yearset for each row of the data frame
    analysis_df['impact_yearset'] = nccs_yearsets_simple(
        analysis_df['impact_eventset'],
        n_sim_years, seed=seed
    )

    ### ----------------------------------- ###
    ### CALCULATE INDIRECT ECONOMIC IMPACTS ###
    ### ----------------------------------- ###

    # Generate supply chain impacts from the yearsets
    # Create a folder to output the data
    os.makedirs("results", exist_ok=True)

    # Run the Supply Chain for each country and sector and output the data needed to csv
    for _, row in analysis_df.iterrows():
        try:
            print(f"Calculating indirect impacts for {row['country']} {row['sector']}...")
            supchain = supply_chain_climada(
                get_sector_exposure(sector=row['sector'], country=row['country']),
                row['impact_yearset'],
                impacted_sector=row['sector'],
                io_approach='ghosh'
            )
            dump_supchain_to_csv(supchain, row['haz_type'], row['sector'], scenario, ref_year, row['country'])
        except ValueError as e:
            print(f"Error calculating indirect impacts for {row['country']} {row['sector']}: {e}")
    print("Done!\nTo show the Dashboard run:\nbokeh serve dashboard.py --show")


if __name__ == "__main__":
    # Added a loop to run for each country to have intermediate files
    for country in country_list:
        calc_supply_chain_impacts(
            [country],  # replace by country_list if whole list should be calculated at once
            hazard_list,
            sector_list,
            scenario,
            ref_year,
            n_sim_years
        )
