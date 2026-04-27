import requests
import pandas as pd
import argparse
import time
import os

def snap_to_road(input_csv, output_csv, api_key, sleep_sec=0.1, timeout_sec=20):
    """
    Snaps GPS coordinates to the nearest road using Google Roads API.
    
    Args:
        input_csv (str): Path to CSV with 'latitude', 'longitude'.
        output_csv (str): Path to save snapped coordinates.
        api_key (str): Google Maps Platform API Key.
    """
    try:
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        print(f"Error: {input_csv} not found.")
        return

    if 'latitude' not in df.columns or 'longitude' not in df.columns:
        print("Error: Input CSV must have 'latitude' and 'longitude' columns.")
        return

    # Google Roads API limits: 100 points per request
    chunk_size = 100
    working_df = df.copy().reset_index(drop=True)
    snapped_latitudes = [None] * len(working_df)
    snapped_longitudes = [None] * len(working_df)
    
    print(f"Snapping {len(df)} points to roads...")

    for i in range(0, len(working_df), chunk_size):
        chunk = working_df.iloc[i:i+chunk_size]
        path = "|".join([f"{lat},{lon}" for lat, lon in zip(chunk['latitude'], chunk['longitude'])])

        try:
            response = requests.get(
                "https://roads.googleapis.com/v1/snapToRoads",
                params={"path": path, "interpolate": "false", "key": api_key},
                timeout=timeout_sec
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Warning: API request failed for chunk {i // chunk_size}: {e}")
            continue

        data = response.json()
        snapped_chunk_count = 0
        for point in data.get('snappedPoints', []):
            original_index = point.get('originalIndex')
            if original_index is None:
                continue
            if not (0 <= original_index < len(chunk)):
                continue

            row_index = chunk.index[original_index]
            loc = point['location']
            snapped_latitudes[row_index] = loc['latitude']
            snapped_longitudes[row_index] = loc['longitude']
            snapped_chunk_count += 1

        if snapped_chunk_count == 0:
            print(f"Warning: No snapped points returned for chunk {i // chunk_size}")

        time.sleep(sleep_sec)

    output_df = working_df.copy()
    output_df['snapped_latitude'] = snapped_latitudes
    output_df['snapped_longitude'] = snapped_longitudes
    output_df['snapped_applied'] = output_df['snapped_latitude'].notna() & output_df['snapped_longitude'].notna()

    output_df.loc[output_df['snapped_applied'], 'latitude'] = output_df.loc[output_df['snapped_applied'], 'snapped_latitude']
    output_df.loc[output_df['snapped_applied'], 'longitude'] = output_df.loc[output_df['snapped_applied'], 'snapped_longitude']

    os.makedirs(os.path.dirname(output_csv) or '.', exist_ok=True)
    output_df.to_csv(output_csv, index=False)
    print(f"Saved {len(output_df)} rows to {output_csv} ({output_df['snapped_applied'].sum()} snapped)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Snap GPS points to roads using Google API")
    parser.add_argument("--input", type=str, required=True, help="Input CSV with lat/lon")
    parser.add_argument("--output", type=str, default="data/snapped_potholes.csv", help="Output CSV")
    parser.add_argument("--key", type=str, required=True, help="Google Maps API Key")
    parser.add_argument("--sleep", type=float, default=0.1, help="Delay between API requests in seconds")
    parser.add_argument("--timeout", type=int, default=20, help="API request timeout in seconds")
    
    args = parser.parse_args()
    
    snap_to_road(args.input, args.output, args.key, args.sleep, args.timeout)
