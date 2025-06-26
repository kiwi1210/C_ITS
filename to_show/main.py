import pandas as pd
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
import folium

denm_metadata = pd.read_csv("denm_vehicle_metadata.csv")
cams_metadata = pd.read_csv("cams_vehicle_metadata.csv")




def standardize_cams_columns(df):
    rename_map = {
        'timestamp': 'timestamp_ms',
        # Keep other CAM columns as is since they are already well named
    }
    return df.rename(columns=rename_map)

def standardize_denm_columns(df):
    rename_map = {
        'originating_station_id': 'station_id',
        'detection_time': 'timestamp_ms',
        'reference_time': 'reference_time_ms',
        # You can rename other columns if you want, e.g.,
        # 'event_latitude_deg': 'latitude_deg',
        # 'event_longitude_deg': 'longitude_deg',
        # 'event_altitude_m': 'altitude_m',
    }
    return df.rename(columns=rename_map)

# Example usage:
cams_metadata_std = standardize_cams_columns(cams_metadata)
denm_metadata_std = standardize_denm_columns(denm_metadata)



# Optionally, rename event location columns in DENM for consistency:
denm_metadata_std = denm_metadata_std.rename(columns={
    'event_latitude_deg': 'latitude_deg',
    'event_longitude_deg': 'longitude_deg',
    'event_altitude_m': 'altitude_m'
})

# Check the results
print("Standardized CAM columns:\n", cams_metadata_std.columns)
print("Standardized DENM columns:\n", denm_metadata_std.columns)


# Save the standardized DataFrames to CSV files
cams_metadata_std.to_csv("standardized_cams_vehicle_metadata.csv", index=False)
denm_metadata_std.to_csv("standardized_denm_vehicle_metadata.csv", index=False)

cams_metadata_std.keys()
denm_metadata_std.keys()



# Example usage:
# cams_metadata_std is your DataFrame with standardized CAM metadata
# map_object = plot_vehicle_positions_on_map(cams_metadata_std)
# map_object.save('vehicle_positions_map.html')

cams_metadata = pd.read_csv("standardized_cams_vehicle_metadata.csv")
denm_metadata = pd.read_csv("standardized_denm_vehicle_metadata.csv")

# Convert it to geopacke 
import geopandas as gpd

cams_metadata_geo = gpd.GeoDataFrame(
    cams_metadata,
    geometry=gpd.points_from_xy(cams_metadata['longitude_deg'], cams_metadata['latitude_deg']),
    crs="EPSG:4326"  # WGS 84
)

denm_metadata_geo = gpd.GeoDataFrame(
    denm_metadata,
    geometry=gpd.points_from_xy(denm_metadata['longitude_deg'], denm_metadata['latitude_deg']),
    crs="EPSG:4326"  # WGS 84
)

# Save the GeoDataFrames to shapefiles
cams_metadata_geo.to_file("cams_vehicle_metadata.gpkg")
denm_metadata_geo.to_file("denm_vehicle_metadata.gpkg")