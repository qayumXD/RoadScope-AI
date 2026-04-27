import pandas as pd
import argparse

def sync_timestamps(detections_csv, gpx_csv, video_start_time_str, output_csv, max_gap_sec=60.0):
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

    if 'timestamp_ms' not in detections.columns:
        print("Error: detections CSV must include a 'timestamp_ms' column.")
        return
    required_gps_cols = {'time', 'latitude', 'longitude'}
    if not required_gps_cols.issubset(gps_data.columns):
        print("Error: GPS CSV must include 'time', 'latitude', and 'longitude' columns.")
        return

    # Parse timestamps
    gps_data['time'] = pd.to_datetime(gps_data['time'], utc=True, errors='coerce')
    gps_data = gps_data.dropna(subset=['time']).sort_values('time').reset_index(drop=True)
    if gps_data.empty:
        print("Error: GPS CSV has no valid timestamps after parsing.")
        return

    detections['timestamp_ms'] = pd.to_numeric(detections['timestamp_ms'], errors='coerce')
    detections = detections.dropna(subset=['timestamp_ms']).copy()
    if detections.empty:
        print("Error: Detections CSV has no valid 'timestamp_ms' values.")
        return
    
    # Video start time
    try:
        video_start_time = pd.to_datetime(video_start_time_str, utc=True)
    except ValueError:
        print("Error: Invalid video start time format. Use ISO 8601 (e.g., '2023-10-27T10:00:00')")
        return

    print(f"Syncing video started at {video_start_time} with {len(gps_data)} GPS points...")

    detections = detections.copy()
    detections['detection_time'] = video_start_time + pd.to_timedelta(detections['timestamp_ms'], unit='ms')
    detections = detections.sort_values('detection_time').reset_index(drop=True)

    merged_data = pd.merge_asof(
        detections,
        gps_data[['time', 'latitude', 'longitude']],
        left_on='detection_time',
        right_on='time',
        direction='nearest',
        tolerance=pd.Timedelta(seconds=max_gap_sec)
    )

    merged_data = merged_data.rename(columns={'time': 'gps_time'})
    merged_data['detection_time'] = merged_data['detection_time'].dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    merged_data['gps_time'] = merged_data['gps_time'].dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
    # Filter out points where GPS sync failed (NaNs)
    synced_count = merged_data['latitude'].notna().sum()
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
    parser.add_argument("--max_gap", type=float, default=60.0, help="Maximum allowed time gap (seconds) when matching GPS points")
    
    args = parser.parse_args()
    
    sync_timestamps(args.detections, args.gpx_csv, args.start_time, args.output, args.max_gap)
