import plotly.express as px
import geopandas as gpd
import pandas as pd

cams_with_city = gpd.read_file("cams_vehicle_metadata_with_city.gpkg")
denm_with_city = gpd.read_file("denm_vehicle_metadata_with_city.gpkg")



# Count number of messages per city for CAM and DENM
cams_counts = cams_with_city['name_city'].value_counts().reset_index()
cams_counts.columns = ['City', 'Number of CAM Messages']
cams_counts['Type'] = 'CAM'

denm_counts = denm_with_city['name_city'].value_counts().reset_index()
denm_counts.columns = ['City', 'Number of CAM Messages']
denm_counts['Type'] = 'DENM'

# Combine into one dataframe
all_counts = pd.concat([cams_counts, denm_counts], ignore_index=True)
all_counts.rename(columns={'Number of CAM Messages': 'Message Count'}, inplace=True)

# Create bar chart
fig = px.bar(
    all_counts,
    x="City",
    y="Message Count",
    color="Type",
    barmode="group",
    title="Number of CAM and DENM Messages per City",
    labels={"City": "City", "Message Count": "Number of Messages"},
    text="Message Count"
)

fig.update_layout(
    xaxis_title="City",
    yaxis_title="Number of Messages",
    legend_title="Message Type",
    template="plotly_white"
)

# Save to HTML
fig.write_html("city_message_stats.html")
