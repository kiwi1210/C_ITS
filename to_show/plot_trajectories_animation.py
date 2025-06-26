import geopandas as gpd
import pandas as pd
from geopy.distance import geodesic
import folium
from folium.plugins import TimestampedGeoJson
from datetime import datetime, timedelta
import json # Import json for saving the GeoJSON

# PARAMETERS
MAX_REALISTIC_SPEED_KMH = 300
TIME_GAP_SECONDS = 120
DISTANCE_GAP_KM = 0.5
PRIMARY_COLOR = '#e63946'
MAX_POINTS_OUTPUT = 100 # New parameter: Maximum number of points in the output trajectory
NUM_INITIAL_POINTS = 10 # Number of points to always include from the start
SPEED_EMPHASIS_FACTOR = 0.9 # Factor to weigh high-speed points for selection (0-1, higher means more emphasis) - Increased for more high-speed emphasis

# --- Data Loading and Preprocessing ---
def load_and_preprocess_data(file_path):
    """Loads vehicle metadata, filters for Salzburg, and preprocesses time/speed."""
    gdf = gpd.read_file(file_path)
    gdf = gdf[gdf["name_city"] == "Salzburg"].copy()

    gdf["speed_kmh"] = gdf["speed_mps"] * 3.6
    gdf["timestamp_ms"] = pd.to_numeric(gdf["timestamp_ms"], errors="coerce")
    gdf.dropna(subset=["timestamp_ms", "geometry"], inplace=True)
    gdf["datetime"] = pd.to_datetime(gdf["timestamp_ms"], unit="ms")
    return gdf

# --- Filter Valid Trajectory Points ---
def filter_valid_trajectory(gdf_data):
    """Filters trajectory points based on time and distance gaps, and realistic speed."""
    valid_indices = []
    for station_id, df in gdf_data.groupby("station_id"):
        df = df.sort_values("datetime").reset_index()
        if len(df) < 2:
            continue
        valid_indices.append(df.loc[0, "index"]) # Always include the first point of each segment
        for i in range(1, len(df)):
            p1, p2 = df.iloc[i - 1], df.iloc[i]
            time_diff = (p2["datetime"] - p1["datetime"]).total_seconds()
            if time_diff <= 0 or time_diff > TIME_GAP_SECONDS:
                continue
            dist_km = geodesic((p1.geometry.y, p1.geometry.x), (p2.geometry.y, p2.geometry.x)).km
            if dist_km > DISTANCE_GAP_KM:
                continue
            if p2["speed_kmh"] > MAX_REALISTIC_SPEED_KMH:
                continue
            valid_indices.append(p2["index"])
    return gdf_data.loc[list(set(valid_indices))].copy()

# --- Select Largest Trajectory ---
def select_largest_trajectory(gdf_filtered):
    """Selects the station_id with the most valid trajectory points."""
    best_id = None
    max_len = -1
    for station_id, df in gdf_filtered.groupby("station_id"):
        if len(df) > max_len:
            max_len = len(df)
            best_id = station_id
    if best_id:
        return gdf_filtered[gdf_filtered["station_id"] == best_id].sort_values("datetime").copy()
    return pd.DataFrame() # Return empty DataFrame if no best_id

# --- Sample Trajectory Points for Output ---
def sample_trajectory_points(df, max_output_points, num_initial_points, speed_emphasis_factor):
    """
    Samples trajectory points to a maximum number, emphasizing initial points and high speed.
    """
    if len(df) <= max_output_points:
        return df

    selected_indices = set()

    # 1. Always include the first N points
    for i in range(min(num_initial_points, len(df))):
        selected_indices.add(df.index[i])

    # 2. Prioritize high-speed points from the rest
    # Calculate a score based on speed (higher speed gets a higher chance of selection)
    # Using a quantile-based approach to get high speed points relative to the dataset
    high_speed_threshold = df['speed_kmh'].quantile(speed_emphasis_factor)
    high_speed_points = df[df['speed_kmh'] >= high_speed_threshold]

    # Add high-speed points, but be mindful of the total limit
    # Convert to list to iterate and add, ensuring not to exceed the limit
    high_speed_candidate_indices = high_speed_points.index.tolist()
    
    # Randomly shuffle high-speed candidates to avoid bias if there are too many
    import random
    random.shuffle(high_speed_candidate_indices)

    for idx in high_speed_candidate_indices:
        if len(selected_indices) < max_output_points:
            selected_indices.add(idx)
        else:
            break # Stop if we've reached the maximum

    # 3. Fill remaining slots with more evenly distributed points if needed
    remaining_points_to_select = max_output_points - len(selected_indices)
    if remaining_points_to_select > 0:
        # Exclude already selected points from the pool for even distribution
        pool_for_even_distribution = df[~df.index.isin(selected_indices)]
        
        if not pool_for_even_distribution.empty:
            # Calculate step size for even distribution
            step = max(1, len(pool_for_even_distribution) // remaining_points_to_select)
            for i in range(0, len(pool_for_even_distribution), step):
                if len(selected_indices) < max_output_points:
                    selected_indices.add(pool_for_even_distribution.iloc[i].name) # Use .name for index
                else:
                    break

    # Reconstruct the DataFrame with selected points and sort by datetime
    sampled_df = df.loc[list(selected_indices)].sort_values("datetime").copy()
    return sampled_df

# --- Build GeoJSON Features ---
def build_geojson_features(df_data):
    """Converts a DataFrame of trajectory points into GeoJSON features."""
    features = []
    # Ensure strictly increasing UTC timestamps for accurate animation
    df_data["datetime"] = df_data["datetime"].dt.tz_localize("UTC")
    times = df_data["datetime"].tolist()
    for i in range(1, len(times)):
        if times[i] <= times[i - 1]:
            # Add a small timedelta to ensure strict increase
            times[i] = times[i - 1] + timedelta(milliseconds=100)
    df_data["datetime"] = times

    for _, row in df_data.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row.geometry.x, row.geometry.y],
            },
            "properties": {
                "time": row["datetime"].isoformat(),
                "speed": row["speed_kmh"], # Added speed to GeoJSON properties
                "icon": "circle",
                "iconstyle": {
                    "fillColor": PRIMARY_COLOR,
                    "fillOpacity": 0.8,
                    "stroke": "true",
                    "radius": 5
                },
            }
        })
    return {
        "type": "FeatureCollection",
        "features": features
    }

# --- Main execution flow ---
if __name__ == "__main__":
    # Define the path to your input data
    input_gpkg_path = "cams_vehicle_metadata_with_city.gpkg"
    output_geojson_path = "salzburg_largest_trajectory.geojson"

    # 1. Load and preprocess data
    gdf = load_and_preprocess_data(input_gpkg_path)
    
    # 2. Filter valid trajectory points
    gdf_filtered = filter_valid_trajectory(gdf)
    
    # 3. Select the largest trajectory
    best_df = select_largest_trajectory(gdf_filtered)


    if not best_df.empty:
        # 4. Sample points to reduce size while emphasizing high speed and start
        # Ensure we don't try to select more points than available
        effective_max_points = min(MAX_POINTS_OUTPUT, len(best_df))
        
        sampled_best_df = sample_trajectory_points(
            best_df,
            effective_max_points,
            NUM_INITIAL_POINTS,
            SPEED_EMPHASIS_FACTOR
        )
        print(f"Original trajectory points: {len(best_df)}")
        print(f"Sampled trajectory points: {len(sampled_best_df)}")

        # 5. Build GeoJSON features
        geojson_output = build_geojson_features(sampled_best_df)
        
        # 6. Save the GeoJSON to a file
        with open(output_geojson_path, "w") as f:
            json.dump(geojson_output, f, indent=4)
        print(f"Generated {output_geojson_path} with {len(geojson_output['features'])} points.")
    else:
        print("No valid trajectory found for Salzburg after filtering.")
