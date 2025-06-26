import folium
import pandas as pd
import numpy as np

def plot_vehicle_positions_on_map(cams_df: pd.DataFrame, map_center: tuple = (47.8, 13.0), zoom_start: int = 12) -> folium.Map:
    """
    Create an interactive Folium map showing vehicle positions from CAM data.
    Points are color-coded by vehicle speed.
    
    Parameters:
    - cams_df: pd.DataFrame with at least 'latitude_deg', 'longitude_deg', 'speed_mps', and 'timestamp_ms' columns.
    - map_center: tuple of (latitude, longitude) for initial map center.
    - zoom_start: int initial zoom level.
    
    Returns:
    - folium.Map object with plotted vehicle positions.
    """
    
    # Create a base Folium map
    fmap = folium.Map(location=map_center, zoom_start=zoom_start, tiles='cartodbpositron')
    
    # Normalize speeds for color mapping (e.g., from 0 to max speed)
    max_speed = cams_df['speed_mps'].max()
    min_speed = cams_df['speed_mps'].min()
    speed_range = max_speed - min_speed if max_speed > min_speed else 1
    
    def speed_to_color(speed: float) -> str:
        """
        Convert speed to a color scale from green (slow) to red (fast).
        """
        # Normalize speed between 0 and 1
        norm_speed = (speed - min_speed) / speed_range
        # Calculate RGB components
        r = int(255 * norm_speed)
        g = int(255 * (1 - norm_speed))
        b = 0
        return f'#{r:02x}{g:02x}{b:02x}'
    
    # Iterate over rows and add markers
    for _, row in cams_df.iterrows():
        lat = row['latitude_deg']
        lon = row['longitude_deg']
        speed = row['speed_mps']
        timestamp = pd.to_datetime(row['timestamp_ms'], unit='ms')
        heading = row.get('heading_deg', 'N/A')
        popup_text = (
            f"<b>Speed:</b> {speed:.2f} m/s<br>"
            f"<b>Heading:</b> {heading}°<br>"
            f"<b>Timestamp:</b> {timestamp}<br>"
            f"<b>Latitude:</b> {lat:.6f}<br>"
            f"<b>Longitude:</b> {lon:.6f}"
        )
        
        folium.CircleMarker(
            location=(lat, lon),
            radius=5,
            color=speed_to_color(speed),
            fill=True,
            fill_color=speed_to_color(speed),
            fill_opacity=0.7,
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(fmap)
    
    return fmap
