from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse
import matplotlib.pyplot as plt
import networkx as nx
import io
import base64
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np

# Create a FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Vue.js default port
    allow_methods=["*"],
    allow_headers=["*"],
)

G = nx.Graph()
stations_df = pd.read_csv("stations.csv")
edges_df = pd.read_csv("edges.csv")

stations_start = dict(zip(stations_df['station_name'], zip(stations_df['latitude'], stations_df['longitude'])))
edges_start = [tuple(row) for row in edges_df[['station1', 'station2', 'line']].itertuples(index=False, name=None)]

def create_figure(G, stations, edges):
    plt.clf()  # Clear the current figure
    G.clear()
    line_colors = {
        "Bakerloo": (137 / 255, 78 / 255, 36 / 255),
        "Central": (220/255, 36/255, 31/255),
        "Jubilee": (134/255, 143/255, 152/255),
        "Piccadilly": (0, 25/255, 168/255),
        "Victoria": (0, 160/255, 226/255)
    }

    # Haversine formula to calculate distance between two sets of lat/long
    def haversine(lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        r = 6371  # Radius of Earth in kilometers
        return c * r
    for name, (lat, lon) in stations.items():
        G.add_node(name, pos=(lon, lat))
    for station1, station2, line_name in edges:
        lat1, lon1 = stations[station1]
        lat2, lon2 = stations[station2]
        distance = round(haversine(lat1, lon1, lat2, lon2), 2)
        G.add_edge(station1, station2, weight=distance, line=line_name, color=line_colors[line_name])


    fig = plt.figure(figsize=(80, 50))

    # Create legend handles dynamically based on the line_colors dictionary
    legend_handles = [
        plt.Line2D([0], [0], color=color, lw=8, label=f"{line} Line") 
        for line, color in line_colors.items()
    ]

    # Append the intersection node handle to the legend_handles list
    legend_handles.append(plt.Line2D(
        [0], [0], 
        marker='o',            # Circle marker
        color='white',         # Face color (background of marker)
        markeredgecolor='black', # Border color
        markeredgewidth='7.5',
        markersize=40,         # Marker size
        label='Intersection Station'
    ))
    edge_weights = [G[u][v]['weight'] for u, v in G.edges]

    total_length = sum(edge_weights)
    average_distance = np.mean(edge_weights)
    std_deviation = np.std(edge_weights)

    # Add metrics as text entries in the legend
    legend_handles.append(plt.Line2D(
        [0], [0],
        color='none',  # No line
        label=f"Total Length: {total_length:.2f} km"
    ))
    legend_handles.append(plt.Line2D(
        [0], [0],
        color='none',  # No line
        label=f"Average Distance: {average_distance:.2f} km"
    ))
    legend_handles.append(plt.Line2D(
        [0], [0],
        color='none',  # No line
        label=f"Std Deviation: {std_deviation:.2f} km"
    ))
    plt.legend(handles=legend_handles, loc="lower right", fontsize=40)

    """
    Station name
    """
    pos = nx.get_node_attributes(G, 'pos')

    nx.draw_networkx_edges(G, pos, width=3, edge_color=[G[u][v]['color'] for u, v in G.edges])

    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G,pos,edge_labels=labels, font_size=8)

    scale = 0.001
    custom_stations_with_offset = pd.read_csv('stations_with_offsets2.csv')
    station_offsets = {}
    for _, row in custom_stations_with_offset.iterrows():
        station_name = row['station_name']
        offset_x = row['x']
        offset_y = row['y']
        
        if station_name in pos:
            # Plus offset into pos
            station_offsets[station_name] = (pos[station_name][0] + offset_x*scale, pos[station_name][1] + offset_y*scale)

    nx.draw_networkx_labels(G, pos=station_offsets, font_size=8)


    """
    Customize the station marker
    """
    intersecting_stations = []
    for node, degree in G.degree():
        if degree > 2:
            intersecting_stations.append(node)
            continue
        if degree == 2:
            line = set()
            for station1, station2, line_name in edges:
                if station1 == node or station2 == node:
                    line.add(line_name)
            if len(line) >= 2:
                intersecting_stations.append(node)



    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=intersecting_stations,
        node_size=100,         
        node_color='white',
        edgecolors='black',     # Border color
        linewidths=2         # Thickness of the border
    )

    other_stations = [node for node in G if node not in intersecting_stations]

    # Create a dictionary to map each station in other_stations to its color
    station_colors = {}

    # Map the color for each station based on the line from `edges`
    for station1, station2 in G.edges:
        if station1 in other_stations:
            station_colors[station1] = G[station1][station2]['color']
        if station2 in other_stations:
            station_colors[station2] = G[station1][station2]['color']
    # Generate the color list for other_stations
    other_station_colors = [station_colors[station] for station in other_stations]

    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=other_stations,
        node_size=100,           
        node_color=other_station_colors,      
        node_shape='.'           
    )

    # Draw another
    # plt.title("London Tube Lines with Distances (in km)", fontsize=100)



    # Save the figure to a bytes buffer
    buf = io.BytesIO() # Create a temporarily place to store the image generated by matplotlib
    plt.savefig(buf, format="png")
    buf.seek(0) # reset the cursor to the beginning
    plt.close()


    """
    buf.read(): Reads the entire binary content of the buffer.
	base64.b64encode(): Encodes the binary image data into a base64 string (safely transmitted as JSON).
	decode(): Converts the base64 bytes object to a string format.
    """
    return base64.b64encode(buf.read()).decode()

# Function to get the line from edges_start
def get_line_from_edges(edges, station1, station2):
    # Check for (station1, station2) or (station2, station1) in edges_start
    for edge in edges:
        if (edge[0] == station1 and edge[1] == station2) or (edge[0] == station2 and edge[1] == station1):
            return edge[2]  # Return the line
    return None  # Return None if no match is found
@app.get("/")
async def get_map():
    figure_base64 = create_figure(G, stations_start, edges_start)
    return JSONResponse({"figure": figure_base64})

@app.get("/stations")
async def get_stations():
    """Return a list of all station names."""
    # Replace with your actual station list or dictionary
    sorted_station_names = sorted(list(stations_start.keys()))
    return {"stations": sorted_station_names}
@app.post("/route")
async def get_route(start_station: str = Form(...), end_station: str = Form(...)):
    """Calculate and return the travel guideline."""
    try:
        G_subfigure = nx.Graph()
        # Calculate shortest path and distance
        shortest_path = nx.dijkstra_path(G, source=start_station, target=end_station, weight="weight")
        shortest_distance = nx.dijkstra_path_length(G, source=start_station, target=end_station, weight="weight")


        # Generate line change instructions
        guide = []
        guideCnt = 1
        for i in range(len(shortest_path) - 1):
            current_station = shortest_path[i]
            next_station = shortest_path[i + 1]

            # Get line data from edges_start
            currentLine = get_line_from_edges(edges_start, current_station, next_station)

            if i == 0:
                previousLine = currentLine
                guide.append(f"1. Start at {current_station} on {currentLine} line")

            if currentLine != previousLine:
                guideCnt += 1
                guide.append(f"{guideCnt}. At {current_station} station change from line {previousLine} to line {currentLine}.")
                previousLine = currentLine

        filtered_stations = {name: coords for name, coords in stations_start.items() if name in shortest_path}
        # print(filtered_stations)
        # Filter edges
        filtered_edges = [
            (shortest_path[i], shortest_path[i + 1], get_line_from_edges(edges_start, shortest_path[i], shortest_path[i + 1]))
            for i in range(len(shortest_path) - 1)
        ]
        figure_base64 = create_figure(G_subfigure, filtered_stations, filtered_edges)
        return {"path": shortest_path, "distance": f"{shortest_distance:.2f} km", "guide": guide, "figure": figure_base64}
    except nx.NetworkXNoPath:
        return {"error": "No path found between the stations."}
    except nx.NodeNotFound:
        return {"error": "One or both stations are not in the network."}
