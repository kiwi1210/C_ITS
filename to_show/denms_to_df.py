from typing import List, Dict, Any
import pandas as pd
import pathlib
import json

from typing import List, Dict, Any, Optional
import pandas as pd
import json
from typing import Union

def extract_denm_metadata(sample: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """
    Extract key metadata fields from a single DENM sample.
    Accepts a dict or JSON string (auto-parses string).
    """
    # If sample is a JSON string, parse it
    if isinstance(sample, str):
        try:
            sample = json.loads(sample)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {e}")
    
    # Proceed as before
    denm = sample.get('msg', {}).get('denm', {})
    management = denm.get('management', {})
    situation = denm.get('situation', {})
    location = denm.get('location', {})
    header = sample.get('header', {})
    
    action_id = management.get('actionID', {})
    originating_station_id = action_id.get('originatingStationID')
    sequence_number = action_id.get('sequenceNumber')
    detection_time = management.get('detectionTime')
    reference_time = management.get('referenceTime')
    relevance_traffic_direction = management.get('relevanceTrafficDirection')
    station_type = management.get('stationType')
    
    event_position = management.get('eventPosition', {})
    event_latitude = event_position.get('latitude')
    event_longitude = event_position.get('longitude')
    
    altitude_info = event_position.get('altitude', {})
    event_altitude = altitude_info.get('altitudeValue')
    altitude_confidence = altitude_info.get('altitudeConfidence')
    
    position_conf_ellipse = event_position.get('positionConfidenceEllipse', {})
    semi_major_confidence = position_conf_ellipse.get('semiMajorConfidence')
    semi_minor_confidence = position_conf_ellipse.get('semiMinorConfidence')
    semi_major_orientation = position_conf_ellipse.get('semiMajorOrientation')
    
    event_type = situation.get('eventType', {})
    cause_code = event_type.get('causeCode')
    sub_cause_code = event_type.get('subCauseCode')
    information_quality = situation.get('informationQuality')
    
    traces = location.get('traces', [])
    trace_count = len(traces)
    total_trace_points = sum(len(trace) for trace in traces)
    
    event_latitude_deg = event_latitude / 1e7 if event_latitude is not None else None
    event_longitude_deg = event_longitude / 1e7 if event_longitude is not None else None
    event_altitude_m = event_altitude / 100 if event_altitude is not None else None
    semi_major_orientation_deg = semi_major_orientation / 10 if semi_major_orientation is not None else None
    
    timestamp = sample.get('timestamp')
    
    return {
        "originating_station_id": originating_station_id,
        "sequence_number": sequence_number,
        "detection_time": detection_time,
        "reference_time": reference_time,
        "event_latitude_deg": event_latitude_deg,
        "event_longitude_deg": event_longitude_deg,
        "event_altitude_m": event_altitude_m,
        "altitude_confidence": altitude_confidence,
        "semi_major_confidence": semi_major_confidence,
        "semi_minor_confidence": semi_minor_confidence,
        "semi_major_orientation_deg": semi_major_orientation_deg,
        "relevance_traffic_direction": relevance_traffic_direction,
        "station_type": station_type,
        "cause_code": cause_code,
        "sub_cause_code": sub_cause_code,
        "information_quality": information_quality,
        "trace_count": trace_count,
        "total_trace_points": total_trace_points,
        "timestamp": timestamp,
    }

def denm_samples_to_dataframe(samples: List[Union[Dict[str, Any], str]]) -> pd.DataFrame:
    metadata_list = []
    for idx, sample in enumerate(samples):
        try:
            metadata = extract_denm_metadata(sample)
            metadata_list.append(metadata)
        except (AttributeError, ValueError) as e:
            print(f"Skipping sample at index {idx}: {e}")
            continue
    
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
    DENMS_FOLDER = pathlib.Path("denms_04_07_16-17")
    
    # Read all JSON files from the CAMS folder
    sample_data = read_all_files(DENMS_FOLDER)

    # Convert the sample data to a DataFrame
    sample_df = denm_samples_to_dataframe(sample_data)

    # Save the DataFrame to a CSV file
    sample_df.to_csv("denm_vehicle_metadata.csv", index=False)
