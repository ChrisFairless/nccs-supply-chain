from climada.util.api_client import Client
def get_hazard(haz_type, country_iso3alpha, scenario, ref_year):
    client = Client()
    if haz_type == 'tropical_cyclone':
        if scenario == 'None' and ref_year == 'historical':
            return client.get_hazard(
                haz_type, properties={
                    'country_iso3alpha': country_iso3alpha,
                    'climate_scenario': 'None',
                    'event_type': 'synthetic'
                }
            )
        else:
            return client.get_hazard(
                haz_type, properties={
                    'country_iso3alpha': country_iso3alpha,
                    'climate_scenario': scenario, 'ref_year': str(ref_year)
                }
            )

haz= get_hazard("tropical_cyclone", "USA", "None", "historical")

haz_event_names = haz.event_name

# Search substrings
substring_katrina = "2005298"
# Filter the list to find strings containing the substring
matching_strings = [event_name for event_name in haz_event_names if substring_katrina in event_name]
print(matching_strings)

import matplotlib.pyplot as plt
haz.plot_intensity(event='2005298N12088')
plt.show()
