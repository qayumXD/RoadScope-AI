import requests
import pandas as pd
import argparse
import time

def snap_to_road(input_csv, output_csv, api_key):
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
    snapped_points = []
    
    print(f"Snapping {len(df)} points to roads...")

    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        path = "|".join([f"{lat},{lon}" for lat, lon in zip(chunk['latitude'], chunk['longitude'])])
        
        url = f"https://roads.googleapis.com/v1/snapToRoads?path={path}&interpolate=true&key={api_key}"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'snappedPoints' in data:
                for point in data['snappedPoints']:
                    loc = point['location']
                    snapped_points.append({
                        'latitude': loc['latitude'],
                        'longitude': loc['longitude'],
                        'original_index': point.get('originalIndex') # Optional mapping back
                    })
            else:
                print(f"Warning: No snapped points returned for chunk {i//chunk_size}")
        else:
            print(f"Error: API Request failed with status {response.status_code}: {response.text}")
            break
        
        time.sleep(0.1) # Be nice to the API

    # Create new DataFrame
    # Note: 'interpolate=true' might return MORE points than input if gaps are large.
    # If strictly mapping 1-to-1, logic needs to use 'originalIndex' to merge back.
    # For now, we save the smooth path.
    
    snapped_df = pd.DataFrame(snapped_points)
    
    if not snapped_df.empty:
        snapped_df.to_csv(output_csv, index=False)
        print(f"Saved {len(snapped_df)} snapped points to {output_csv}")
    else:
        print("Failed to snap any points.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Snap GPS points to roads using Google API")
    parser.add_argument("--input", type=str, required=True, help="Input CSV with lat/lon")
    parser.add_argument("--output", type=str, default="data/snapped_potholes.csv", help="Output CSV")
    parser.add_argument("--key", type=str, required=True, help="Google Maps API Key")
    
    args = parser.parse_args()
    
    snap_to_road(args.input, args.output, args.key)
