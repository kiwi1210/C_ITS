import geopandas as gpd


cams = gpd.read_file("cams_vehicle_metadata.gpkg")
denm = gpd.read_file("denm_vehicle_metadata.gpkg")
regions = gpd.read_file("spatial_regions.geojson")


# Perform spatial join to assign 'name' from regions to each point as 'name_city'
cams_with_city = gpd.sjoin(cams, regions[['name', 'geometry']], how="left", predicate="within")
cams_with_city = cams_with_city.rename(columns={'name': 'name_city'}).drop(columns=['index_right'])
denm_with_city = gpd.sjoin(denm, regions[['name', 'geometry']], how="left", predicate="within")
denm_with_city = denm_with_city.rename(columns={'name': 'name_city'}).drop(columns=['index_right'])

# Save the updated GeoDataFrames with city names
cams_with_city.to_file("cams_vehicle_metadata_with_city.gpkg")
denm_with_city.to_file("denm_vehicle_metadata_with_city.gpkg")


