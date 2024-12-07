import urllib.request
import json
import pandas as pd
import pickle

# Step 1: Pull data from the API and process it
# Define the color of the Line
line_colors = {
    "Bakerloo": (137/255, 78/255, 36/255),
    "Central": (220/255, 36/255, 31/255),
    "Jubilee": (134/255, 143/255, 152/255),
    "Piccadilly": (0, 25/255, 168/255),
    "Victoria": (0, 160/255, 226/255)
}

stations_data = []
edges_data = []

for line in line_colors.keys():
    urlConnection = f"https://api.tfl.gov.uk/Line/{line.lower()}/Route/Sequence/all"
    with urllib.request.urlopen(urlConnection) as response:
        dataCon = json.loads(response.read().decode())
        stopPointSequences = dataCon.get("stopPointSequences")

        for sequence in stopPointSequences:
            for i in range(len(sequence['stopPoint']) - 1):
                station1 = sequence['stopPoint'][i]
                station2 = sequence['stopPoint'][i + 1]

                station1_name = station1['name']
                station1_lat = station1['lat']
                station1_lon = station1['lon']

                station2_name = station2['name']
                station2_lat = station2['lat']
                station2_lon = station2['lon']

                stations_data.append([station1_name, station1_lat, station1_lon])
                stations_data.append([station2_name, station2_lat, station2_lon])

                edges_data.append([station1_name, station2_name, line])

# Step 2: Data cleaning
stations_df = pd.DataFrame(stations_data, columns=['station_name', 'latitude', 'longitude'])
edges_df = pd.DataFrame(edges_data, columns=['station1', 'station2', 'line'])

stations_df = stations_df.drop_duplicates(subset=['station_name'])
stations_df['station_name'] = stations_df['station_name'].str.replace(' Underground Station', '', regex=False)
edges_df['station1'] = edges_df['station1'].str.replace(' Underground Station', '', regex=False)
edges_df['station2'] = edges_df['station2'].str.replace(' Underground Station', '', regex=False)

# Step 3: Save processed data locally
stations_df.to_csv("stations.csv", index=False)
edges_df.to_csv("edges.csv", index=False)