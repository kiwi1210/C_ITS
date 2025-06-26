import geopandas as gpd
import folium
from folium.plugins import Fullscreen
from shapely.geometry import LineString
import pandas as pd
from geopy.distance import geodesic

# Load data from the provided GeoPackage file
cams = gpd.read_file("cams_vehicle_metadata_with_city.gpkg")
salzburg_cams = cams[cams["name_city"] == "Salzburg"].copy()

# --- Data Cleaning and Preparation ---

# Convert speed from meters/second to km/h and filter out unrealistic speeds
salzburg_cams["speed_kmh"] = salzburg_cams["speed_mps"] * 3.6
salzburg_cams = salzburg_cams[salzburg_cams["speed_kmh"] < 300]

# Ensure timestamp is a numeric type and drop rows with invalid data
salzburg_cams['timestamp_ms'] = pd.to_numeric(salzburg_cams['timestamp_ms'], errors='coerce')
salzburg_cams = salzburg_cams.dropna(subset=['timestamp_ms', 'geometry'])

# --- Speed Classification ---

def classify_speed(speed_kmh):
    """Categorizes speed into predefined classes."""
    if speed_kmh > 140:
        return "critical"
    elif speed_kmh > 60:
        return "fast"
    else:
        return "normal"

salzburg_cams["speed_category"] = salzburg_cams["speed_kmh"].apply(classify_speed)

# --- Styling and Map Initialization ---

# Define styles for each speed category
style_dict = {
    "normal": {"color": "#888888", "opacity": 0.6, "name": "Normal (< 60 km/h)"},
    "fast": {"color": "#ffaa00", "opacity": 0.8, "name": "Fast (60–140 km/h)"},
    "critical": {"color": "#ff0000", "opacity": 1.0, "name": "Critical (> 140 km/h)"}
}

# Get the average coordinates to center the map
mean_lat = salzburg_cams.geometry.y.mean()
mean_lon = salzburg_cams.geometry.x.mean()

# ✨ FIX: Initialize map with `tiles=None` to prevent the default basemap
m = folium.Map(location=[mean_lat, mean_lon], zoom_start=13, control_scale=True, tiles=None)

# Add all desired basemap layers manually
folium.TileLayer('OpenStreetMap', name='OpenStreetMap').add_to(m)
folium.TileLayer('CartoDB Positron', name='Light').add_to(m)
folium.TileLayer('Stamen Toner', name='Dark').add_to(m)
folium.TileLayer('Esri.WorldImagery', name='Satellite').add_to(m)

# Create a feature group for each speed category to allow toggling them
groups = {
    "normal": folium.FeatureGroup(name=style_dict["normal"]["name"], show=True).add_to(m),
    "fast": folium.FeatureGroup(name=style_dict["fast"]["name"], show=True).add_to(m),
    "critical": folium.FeatureGroup(name=style_dict["critical"]["name"], show=True).add_to(m),
}

# --- Trajectory Segmentation and Plotting ---

# Define thresholds for breaking a trajectory into separate segments
TIME_GAP_SECONDS = 120
DISTANCE_GAP_KM = 0.5

# ✨ FIX: Iterate through each vehicle's data to draw colored path segments
for vehicle_id, df in salzburg_cams.groupby("station_id"):
    # Sort points by time to ensure correct order
    df = df.sort_values("timestamp_ms").reset_index(drop=True)
    
    # Need at least two points to draw a line
    if len(df) < 2:
        continue

    # Iterate through consecutive pairs of points
    for i in range(len(df) - 1):
        pt1 = df.iloc[i]
        pt2 = df.iloc[i+1]

        # Check for large gaps in time or distance
        time_gap = (pt2["timestamp_ms"] - pt1["timestamp_ms"]) / 1000
        dist_km = geodesic((pt1.geometry.y, pt1.geometry.x), (pt2.geometry.y, pt2.geometry.x)).km
        
        # If gap is too large, don't draw a line connecting these points
        if time_gap > TIME_GAP_SECONDS or dist_km > DISTANCE_GAP_KM:
            continue

        # Create a line segment between the two points
        line = LineString([pt1.geometry, pt2.geometry])
        
        # Get the speed category and corresponding style for this segment
        category = pt1["speed_category"]
        style = style_dict[category]

        # Draw the GeoJson line on the map, colored by its speed category
        folium.GeoJson(
            data=line.__geo_interface__,
            style_function=lambda x, s=style: {
                'color': s["color"],
                'weight': 4,
                'opacity': s["opacity"]
            }
        ).add_to(groups[category])

# --- Final Touches ---

# Add layer control, fullscreen button, and a custom legend
folium.LayerControl(collapsed=False).add_to(m)
Fullscreen().add_to(m)

legend_html = '''
<div style="position: fixed; bottom: 50px; left: 10px; width: 220px; padding: 10px;
     border: 2px solid grey; background-color: rgba(255, 255, 255, 0.85); z-index:9999; 
     font-size:14px; border-radius: 5px;">
<b>🚗 Vehicle Speed</b><br>
<div style="margin-top: 5px;"><span style="display:inline-block;width:20px;height:6px;background:#888888;opacity:0.6;"></span> Normal (&lt; 60 km/h)</div>
<div><span style="display:inline-block;width:20px;height:6px;background:#ffaa00;opacity:0.8;"></span> Fast (60–140 km/h)</div>
<div><span style="display:inline-block;width:20px;height:6px;background:#ff0000;opacity:1.0;"></span> Critical (&gt; 140 km/h)</div>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Save the final map to an HTML file
m.save("salzburg_trajectories_fixed.html")

print("Map has been generated and saved to 'salzburg_trajectories_fixed.html'")