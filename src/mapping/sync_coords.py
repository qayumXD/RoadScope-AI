import pandas as pd
import argparse
from datetime import timedelta, datetime
import pytz

def sync_timestamps(detections_csv, gpx_csv, video_start_time_str, output_csv):
    """
    Synchronizes detection timestamps with GPS timestamps.
    
    Args:
        detections_csv (str): Path to detections.csv from Phase 2.
        gpx_csv (str): Path to parsed_gps.csv from Phase 3.
        video_start_time_str (str): Start time of the video in UTC (ISO 8601 format).
        output_csv (str): Path to save the merged data.
    """
    # Load data
    try:
        detections = pd.read_csv(detections_csv)
        gps_data = pd.read_csv(gpx_csv)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    # Parse timestamps
    # GPS time should already be UTC from parse_gpx.py, but let's ensure
    gps_data['time'] = pd.to_datetime(gps_data['time'])
    
    # Video start time
    try:
        video_start_time = pd.to_datetime(video_start_time_str).replace(tzinfo=pytz.UTC)
    except ValueError:
        print("Error: Invalid video start time format. Use ISO 8601 (e.g., '2023-10-27T10:00:00')")
        return

    print(f"Syncing video started at {video_start_time} UTC with {len(gps_data)} GPS points...")

    # Function to find nearest GPS point
    def get_lat_lot(row):
        # Calculate absolute time of this detection
        # timestamp_ms is from the start of the video
        detection_time = video_start_time + timedelta(milliseconds=row['timestamp_ms'])
        
        # Find nearest GPS point by time
        # This is a naive nearest neighbor search. For production, use `pd.merge_asof`.
        # Ensure GPS data is sorted
        gps_data_sorted = gps_data.sort_values('time')
        
        # Use merge_asof logic manually or use index search
        # Calculate time difference
        time_diff = (gps_data_sorted['time'] - detection_time).abs()
        
        # Find index of minimum difference
        min_idx = time_diff.idxmin()
        nearest_point = gps_data_sorted.loc[min_idx]
        
        # Threshold: if difference is too large (e.g. > 5 seconds), GPS might be missing
        if time_diff[min_idx].total_seconds() > 5.0:
            return None, None
            
        return nearest_point['latitude'], nearest_point['longitude']

    # Apply to all detections
    # Note: iterating rows is slow for large datasets, vectorization is better but more complex to explain/implement quickly.
    # For a prototype, this is fine.
    
    merged_data = detections.copy()
    merged_data[['latitude', 'longitude']] = merged_data.apply(
        lambda row: pd.Series(get_lat_lot(row)), axis=1
    )
    
    # Filter out points where GPS sync failed (NaNs)
    synced_count = merged_data['latitude'].count()
    print(f"Successfully synced {synced_count} / {len(merged_data)} detections.")
    
    if synced_count > 0:
        merged_data.to_csv(output_csv, index=False)
        print(f"Saved synchronized data to {output_csv}")
    else:
        print("Warning: No detections were successfully synced. Check video_start_time and GPS coverage.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync Video Detections with GPS Track")
    parser.add_argument("--detections", type=str, required=True, help="Path to detections.csv")
    parser.add_argument("--gpx_csv", type=str, required=True, help="Path to parsed GPS CSV")
    parser.add_argument("--start_time", type=str, required=True, help="Video start UTC time (ISO 8601, e.g. 2023-10-27T14:30:00)")
    parser.add_argument("--output", type=str, default="data/mapped_potholes.csv", help="Output path")
    
    args = parser.parse_args()
    
    sync_timestamps(args.detections, args.gpx_csv, args.start_time, args.output)
