import folium
import branca.colormap as cm
from branca.colormap import LinearColormap
import requests
import numpy as np
from geopy.geocoders import Nominatim
import pycountry
import pandas as pd
from googletrans import Translator
from fuzzywuzzy import process
import matplotlib.pyplot as plt

# Function to fetch GeoJSON data for all countries
def get_geojson_data():
    """
    Fetches GeoJSON data for all countries.
    """
    return requests.get('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json').json()

# Function to create a mapping between English names and real country names
def create_mapping(english_countries, real_names):
    """
    Creates a mapping between English names and real country names while maintaining the order.
    """
    name_mapping = {}
    for english_name in english_countries:
        closest_match = process.extractOne(english_name, real_names)[0]
        name_mapping[english_name] = closest_match
    return name_mapping

# Function to update the dictionary with the new keys
def update_country_dict(mapping, country_total):
    """
    Updates the dictionary with the new keys.
    """
    dict_countries = {}
    dict_countries.update(zip(mapping.values(), country_total.values()))
    return dict_countries

# Load the population data
sp2024 = pd.read_excel('sp2024.xlsx', skiprows=7)
sp2024.columns = ['Country', 'Total']
sp2024 = sp2024.dropna(subset=['Total'])
sp2024['Total'] = sp2024['Total'].astype(int)
country_total = dict(zip(sp2024['Country'], sp2024['Total']))

# Translate Spanish country names to English
translator = Translator()
spanish_countries = list(country_total.keys())
english_countries = [translator.translate(country, src='es', dest='en').text for country in spanish_countries]

# Create a map centered around the world
m = folium.Map(location=[0, 0], zoom_start=2)

# Fetch GeoJSON data for all countries
geo_json_data = get_geojson_data()

# Extract the real names of countries from the GeoJSON data
real_names = [feature['properties']['name'] for feature in geo_json_data['features']]

# Create a mapping between English names and real names while maintaining the order
name_mapping = create_mapping(english_countries, real_names)

# Replace the English names with the real names using the mapping
english_countries = [name_mapping[english_name] for english_name in english_countries]

# Update the dictionary with the new keys
dict_countries = update_country_dict(name_mapping, country_total)

# Add countries that are not processed
dict_countries.update({
    'Republic of the Congo': 11,
    'Estonia': 410,
    'Moldova': 11,
    'Slovakia': 469,
    'Andorra': 27679,
    'Western Sahara': 10,
    'Guyana': 13,
    'El Salvador': 2877
})

# Filter out features for the countries we need
features = [feature for feature in geo_json_data['features'] if feature['properties']['name'] in dict_countries]

# Find min and max values for normalization
min_value = min(dict_countries.values())
max_value = max(dict_countries.values())
values = np.array(list(dict_countries.values()))

# Calculate percentiles
percentiles = list(range(0, 101, 2))
percentile_values = [np.percentile(values, p) for p in percentiles]

# Define colors for the gradient from light yellow to dark red, one for each percentile
colors = ['#FFFFCC', '#FFFFB2', '#FFFF99', '#FFFF7F', '#FFFF66', '#FFFF4C', '#FFFF33', '#FFFF1A',
          '#FFFF00', '#FFEC00', '#FFE600', '#FFE000', '#FFDA00', '#FFD400', '#FFCE00', '#FFC800',
          '#FFC200', '#FFBC00', '#FFB600', '#FFB000', '#FFAA00', '#FFA400', '#FF9E00', '#FF9800',
          '#FF9200', '#FF8C00', '#FF8600', '#FF8000', '#FF7A00', '#FF7400', '#FF6E00', '#FF6800',
          '#FF6200', '#FF5C00', '#FF5600', '#FF5000', '#FF4A00', '#FF4400', '#FF3E00', '#FF3800',
          '#FF3200', '#FF2C00', '#FF2600', '#FF2000', '#FF1A00', '#FF1400', '#FF0E00', '#FF0800',
          '#FF0000']

# Create a LinearColormap with custom color stops
colormap = LinearColormap(colors, vmin=min_value, vmax=max_value)
colormap.percentiles = percentiles

# Create a geocoder instance
geolocator = Nominatim(user_agent="spanish_population_map")

# Add GeoJSON layers for each country with a gradient color based on their values
for feature in features:
    country_name = feature['properties']['name']
    value = dict_countries.get(country_name)
    if value is not None:        
        folium.GeoJson(
            feature,
            name=country_name,
            style_function=lambda feature, value=value:
                {
                    'color': 'black',  # Border color
                    'weight': 0.5,       # Border weight
                    'fillOpacity': 0.5,  # Opacity of the fill color
                    'fillColor': colormap(value)  # Fill color based on the value
                }
        ).add_to(m)

# Set the HTML content for the caption
colormap.caption = 'Spanish population residing abroad'

# Add the colormap to the map
m.add_child(colormap)
m.save("world_2024.html")

# Extract the top 5 countries with more Spanish people
sorted_dict = dict(sorted(dict_countries.items(), key=lambda item: item[1], reverse=True))
top5 = dict(list(sorted_dict.items())[:5])

# Replace 'United States of America' with 'USA'
try:
    top5['USA'] = top5.pop('United States of America')
except KeyError:
    pass

top5 = dict(sorted(top5.items(), key=lambda item: item[1], reverse=True))

# Extracting country names and values
countries = list(top5.keys())
values = list(top5.values())

# Create horizontal bar plot
plt.figure(figsize=(12, 12))
bars = plt.barh(range(len(countries)), values, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])

# Adding value at the edge of each bar
for bar, value in zip(bars, values):
    plt.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f'{value:,}', ha='left', va='center', fontsize=12, fontname='Arial')

plt.xlabel('Population', fontsize=14, fontweight='bold', fontname='Arial')
plt.ylabel('Countries', fontsize=14, fontweight='bold', fontname='Arial')
plt.title('Top 5 Countries with More Spanish People', fontsize=16, fontweight='bold', fontname='Arial')
plt.gca().invert_yaxis()
plt.xticks(fontsize=12, fontname='Arial')
plt.yticks(range(len(countries)), countries, fontsize=12, fontname='Arial')  # Set country names as y-tick labels
plt.grid(axis='x', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

# Save the plot
plt.savefig("top_5_countries.png")
