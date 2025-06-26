# Visualizing C-ITS Data from Vehicles — Group Project Report

## Project Overview

Historic datasets of Cooperative Awareness Messages (CAMs) and Decentralized Environmental Notification Messages (DENMs) collected from vehicles in Salzburg. CAMs consist of periodic messages that provide GPS coordinates along with dynamic vehicle information, while DENMs are event-driven messages that report special traffic events such as stationary vehicles or traffic jams.

## Methodology & Workflow

### Data Preprocessing


We started by cleaning and parsing the C-ITS datasets, focusing on the CAM and DENM messages—both of which are nested JSON structures with key metadata spread across multiple levels. The goal was to extract only the fields needed for spatial-temporal analysis and visualization. We handled inconsistent or incomplete messages with robust error checks and filtered out irrelevant or redundant fields, such as status flags or confidence indicators that did not add value. Spatial data (latitude, longitude, altitude) was standardized to WGS84 using scaling factors, ensuring compatibility with GIS tools. From CAM messages, we extracted spatial coordinates, timestamps (in UNIX epoch milliseconds), and vehicle dynamics (speed, heading, acceleration, curvature, steering angle). From DENM messages, we pulled out event types, positions, validity periods, traffic relevance, and unique vehicle/station identifiers for grouping and analysis. The cleaned data was stored in a single Pandas DataFrame, where each row represents one message. The DataFrame schema is as follows:


#### CAM Metadata Fields


| Column Name                      | Description                                                   | Data Type          |
| -------------------------------- | ------------------------------------------------------------- | ------------------ |
| latitude\_deg                    | Latitude of the vehicle in decimal degrees (WGS84)            | float              |
| longitude\_deg                   | Longitude of the vehicle in decimal degrees (WGS84)           | float              |
| altitude\_m                      | Altitude of the vehicle above mean sea level, in meters       | float              |
| heading\_deg                     | Vehicle heading angle relative to true north, in degrees      | float              |
| speed\_mps                       | Vehicle speed in meters per second                            | float              |
| speed\_confidence                | Confidence level of the speed measurement                     | float or int       |
| lateral\_acceleration\_mps2      | Lateral (sideways) acceleration of the vehicle, in m/s²       | float              |
| longitudinal\_acceleration\_mps2 | Longitudinal (forward/backward) acceleration, in m/s²         | float              |
| yaw\_rate\_deg\_per\_s           | Rate of change of yaw angle, degrees per second               | float              |
| vehicle\_length\_m               | Vehicle length in meters                                      | float              |
| vehicle\_width\_m                | Vehicle width in meters                                       | float              |
| drive\_direction                 | Drive direction indicator (e.g., forward, reverse)            | int or categorical |
| station\_id                      | Unique identifier for the transmitting station or vehicle     | string/int         |
| station\_type                    | Type/class of station or vehicle (e.g., passenger car, truck) | string/int         |
| timestamp\_ms                    | Message timestamp in UNIX epoch milliseconds                  | int                |
| path\_history\_length            | Number of previous positions recorded in the path history     | int                |


#### DENM Metadata Fields

| Column Name                   | Description                                                                     | Data Type          |
| ----------------------------- | ------------------------------------------------------------------------------- | ------------------ |
| station\_id                   | Unique identifier of the originating station or vehicle                         | string/int         |
| sequence\_number              | Sequence number identifying message order or version                            | int                |
| timestamp\_ms                 | Detection time of the event in UNIX epoch milliseconds                          | int                |
| reference\_time\_ms           | Reference time related to the event, in UNIX epoch milliseconds                 | int                |
| latitude\_deg                 | Latitude of the event location in decimal degrees                               | float              |
| longitude\_deg                | Longitude of the event location in decimal degrees                              | float              |
| altitude\_m                   | Altitude of the event location above mean sea level, in meters                  | float              |
| relevance\_traffic\_direction | Traffic direction relevance of the event (e.g., same direction, all directions) | int or categorical |
| station\_type                 | Type or class of station or vehicle originating the message                     | string/int         |
| cause\_code                   | Numeric code indicating the cause or type of reported event                     | int                |
| sub\_cause\_code              | Additional detail on the cause type                                             | int                |
| information\_quality          | Quality indicator of the event information                                      | int or categorical |
| trace\_count                  | Number of traces (paths) associated with the event                              | int                |
| total\_trace\_points          | Total number of trace points across all traces                                  | int                |


### Study Area & Data Collection Zones

The CAM and DENM messages were collected from vehicles operating across various regions in and around Salzburg, Austria. The figure below shows a side-by-side comparison of CAM (left) and DENM (right) message distributions, overlaid on a satellite map. Each red polygon highlights an area where C-ITS messages were recorded. Purple markers represent individual messages (or clusters thereof), indicating both high-traffic urban centers and more remote, alpine transit corridors. CAMs (left map) show continuous, dense coverage, especially along major roadways, reflecting the periodic nature of these messages. DENMs (right map) appear more sparsely and are concentrated in areas where specific traffic events occurred, such as hazards. These spatial patterns illustrate the complementary nature of CAM and DENM data—while CAMs offer high-frequency motion tracking, DENMs capture rare but important incident-based information.

<p align="center"> <img src="images/map_init.png" alt="CAM and DENM message locations in Salzburg region" width="800"> </p>

### Simple stats

The following interactive bar chart summarizes the number of CAM and DENM messages recorded per city. CAM messages, which are sent periodically by vehicles, dominate the total volume. In contrast, DENM messages are event-triggered and occur less frequently, appearing primarily in cities with more complex traffic situations. This distribution provides insight into both baseline traffic flow (via CAMs) and abnormal events (via DENMs).

<iframe src="images/city_stats.html" width="100%" height="600" frameborder="0"></iframe>