import gpxpy
import pandas as pd
import argparse
import os

def parse_gpx(gpx_file_path):
    """
    Parses a GPX file and extracts latitude, longitude, and timestamps.
    
    Args:
        gpx_file_path (str): Path to the GPX file.
    
    Returns:
        pd.DataFrame: DataFrame containing 'time', 'latitude', 'longitude', 'elevation'.
    """
    try:
        with open(gpx_file_path, 'r', encoding='utf-8') as gpx_file:
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
    if df.empty:
        print(f"Warning: No track points found in {gpx_file_path}")
        return df
    
    # Normalize timestamps and ensure they are UTC timezone-aware.
    df['time'] = pd.to_datetime(df['time'], utc=True, errors='coerce')
    invalid_time_count = df['time'].isna().sum()
    if invalid_time_count > 0:
        print(f"Warning: Dropping {invalid_time_count} GPX points with invalid timestamps.")
        df = df.dropna(subset=['time']).copy()

    df = df.sort_values('time').reset_index(drop=True)
        
    print(f"Parsed {len(df)} points from {gpx_file_path}")
    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse GPX file to CSV")
    parser.add_argument("--gpx", type=str, required=True, help="Path to GPX file")
    parser.add_argument("--output", type=str, default="data/gps_logs/parsed_gps.csv", help="Path to output CSV")
    
    args = parser.parse_args()

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    df = parse_gpx(args.gpx)
    if df is not None:
        df.to_csv(args.output, index=False)
        print(f"Saved parsed data to {args.output}")
