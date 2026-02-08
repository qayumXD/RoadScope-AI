import gpxpy
import pandas as pd
import argparse
from datetime import datetime

def parse_gpx(gpx_file_path):
    """
    Parses a GPX file and extracts latitude, longitude, and timestamps.
    
    Args:
        gpx_file_path (str): Path to the GPX file.
    
    Returns:
        pd.DataFrame: DataFrame containing 'time', 'latitude', 'longitude', 'elevation'.
    """
    try:
        with open(gpx_file_path, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
    except FileNotFoundError:
        print(f"Error: File {gpx_file_path} not found.")
        return None

    data = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                data.append({
                    'time': point.time,
                    'latitude': point.latitude,
                    'longitude': point.longitude,
                    'elevation': point.elevation
                })
    
    df = pd.DataFrame(data)
    
    # Ensure time is in UTC and timezone-aware
    if not df.empty and df['time'].dt.tz is None:
        df['time'] = df['time'].dt.tz_localize('UTC')
        
    print(f"Parsed {len(df)} points from {gpx_file_path}")
    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse GPX file to CSV")
    parser.add_argument("--gpx", type=str, required=True, help="Path to GPX file")
    parser.add_argument("--output", type=str, default="data/gps_logs/parsed_gps.csv", help="Path to output CSV")
    
    args = parser.parse_args()
    
    df = parse_gpx(args.gpx)
    if df is not None:
        df.to_csv(args.output, index=False)
        print(f"Saved parsed data to {args.output}")
