from climada.util.api_client import Client
import climada.util.coordinates as u_coord
import pandas as pd

country_list = ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda', 'Argentina',
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
                'Zimbabwe']

out_list = []
client = Client()
client.online = False

for country in country_list:
    print(country)
    bbox = (180, 90, -180, -90)
    try:
        exp = client.get_litpop(country)
        exp_bbox = u_coord.latlon_bounds(
                    exp.gdf.latitude.values, exp.gdf.longitude.values, buffer=0.5)
        bbox = (min(bbox[0], exp_bbox[0]), min(bbox[1], exp_bbox[1]), max(bbox[2], exp_bbox[2]), max(bbox[3], exp_bbox[3]))
    except Exception as e:
        print("That didn't work")
        print(e)
        continue
    print(country)
    print(bbox)
    if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
        print("Couldn't figure out a bounding box")
        continue
    out_list = out_list + [{'country': country, 'lon_min': bbox[0], 'lat_min': bbox[1], 'lon_max': bbox[2], 'lat_max': bbox[3]}]

pd.DataFrame(out_list).to_csv('./data/country_bounding_boxes.csv')

