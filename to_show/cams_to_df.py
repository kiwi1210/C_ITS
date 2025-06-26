from typing import List, Dict, Any
import pandas as pd
import pathlib
import json

def extract_vehicle_metadata(sample: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts key metadata fields from a single vehicle movement JSON sample.
    
    Parameters
    ----------
    sample : Dict[str, Any]
        A dictionary representing the JSON structure of a single vehicle message.
    
    Returns
    -------
    Dict[str, Any]
        A dictionary containing extracted metadata fields with appropriate units and types.
    """
    cam_params = sample['msg']['cam']['camParameters']
    basic_container = cam_params['basicContainer']
    ref_pos = basic_container['referencePosition']
    high_freq = cam_params['highFrequencyContainer']['basicVehicleContainerHighFrequency']
    low_freq = cam_params['lowFrequencyContainer']['basicVehicleContainerLowFrequency']
    header = sample['msg']['header']
    
    # Extract and convert position (WGS84)
    latitude = ref_pos['latitude'] / 1e7
    longitude = ref_pos['longitude'] / 1e7
    altitude = ref_pos['altitude']['altitudeValue'] / 100.0  # Convert cm to meters
    
    # Extract heading, speed, accelerations, yaw rate (scaled units)
    heading = high_freq['heading']['headingValue'] / 100.0  # degrees
    speed = high_freq['speed']['speedValue'] / 10.0  # m/s (from decimeters per second)
    lateral_acc = high_freq['lateralAcceleration']['lateralAccelerationValue'] / 100.0  # m/s²
    longitudinal_acc = high_freq['longitudinalAcceleration']['longitudinalAccelerationValue'] / 100.0  # m/s²
    yaw_rate = high_freq['yawRate']['yawRateValue'] / 100.0  # degrees per second
    
    # Vehicle dimensions
    vehicle_length = high_freq['vehicleLength']['vehicleLengthValue']  # meters (assumed)
    vehicle_width = high_freq.get('vehicleWidth', None)  # meters, may be None
    
    # Confidence values (categorical or numeric)
    altitude_conf = ref_pos['altitude']['altitudeConfidence']
    heading_conf = high_freq['heading']['headingConfidence']
    speed_conf = high_freq['speed']['speedConfidence']
    
    # Additional metadata
    drive_direction = high_freq['driveDirection']
    station_id = header['stationID']
    station_type = basic_container.get('stationType', None)
    timestamp = sample.get('timestamp', None)
    
    # Optionally, summarize path history length (count of deltas)
    path_history = low_freq.get('pathHistory', [])
    path_history_length = len(path_history)
    
    # Build a metadata dictionary
    metadata = {
        'latitude_deg': latitude,
        'longitude_deg': longitude,
        'altitude_m': altitude,
        'altitude_confidence': altitude_conf,
        'heading_deg': heading,
        'heading_confidence': heading_conf,
        'speed_mps': speed,
        'speed_confidence': speed_conf,
        'lateral_acceleration_mps2': lateral_acc,
        'longitudinal_acceleration_mps2': longitudinal_acc,
        'yaw_rate_deg_per_s': yaw_rate,
        'vehicle_length_m': vehicle_length,
        'vehicle_width_m': vehicle_width,
        'drive_direction': drive_direction,
        'station_id': station_id,
        'station_type': station_type,
        'timestamp': timestamp,
        'path_history_length': path_history_length
    }
    
    return metadata

def samples_to_dataframe(samples: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Converts a list of vehicle movement JSON samples into a pandas DataFrame 
    containing extracted and processed metadata for each sample.
    
    Parameters
    ----------
    samples : List[Dict[str, Any]]
        A list of dictionaries, each representing a vehicle movement JSON sample.
    
    Returns
    -------
    pd.DataFrame
        A DataFrame with each row representing one sample and columns for each metadata field.
    """
    # Extract metadata for all samples
    metadata_list = []
    for idx, sample in enumerate(samples):
        try:
            metadata = extract_vehicle_metadata(sample)
            metadata_list.append(metadata)
        except KeyError as e:
            # Log or handle missing keys per sample, skipping invalid entries here
            print(f"Warning: Missing key {e} in sample index {idx}. Skipping this sample.")
        except Exception as e:
            print(f"Error processing sample index {idx}: {e}. Skipping this sample.")
    
    # Create DataFrame
    df = pd.DataFrame(metadata_list)
    
    return df


def read_all_files(folder: pathlib.Path) -> List[Dict[str, Any]]:
    """
    Reads all JSON files in a specified folder and returns their contents as a list of dictionaries.
    
    Parameters
    ----------
    folder : pathlib.Path
        The folder containing JSON files to read.
    
    Returns
    -------
    List[Dict[str, Any]]
        A list of dictionaries, each representing the content of a JSON file.
    """
    json_files = list(folder.glob("*.json"))
    data = []
    
    for file in json_files:
        with open(file, 'r') as f:
            try:
                content = json.load(f)
                data.append(content)
            except json.JSONDecodeError as e:
                print(f"Error reading {file}: {e}")
    data = [item for sublist in data for item in sublist] if data else []
    return data

if __name__ == "__main__":

    # Set the GLOBAL parameters
    CAMS_FOLDER = pathlib.Path("cams_04_07_16-17")

    # Read all JSON files from the CAMS folder
    sample_data = read_all_files(CAMS_FOLDER)

    # Convert the sample data to a DataFrame
    df = samples_to_dataframe(sample_data)

    # Save the DataFrame to a CSV file
    df.to_csv("cams_vehicle_metadata.csv", index=False)

