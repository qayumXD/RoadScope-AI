import pandas as pd
import numpy as np
import argparse
from datetime import datetime, timedelta
import os

def generate_mock_gps(output_gpx_path, start_time, duration_sec=60, points_per_sec=1):
    """
    Generates a mock GPX file with a path.
    """
    num_points = duration_sec * points_per_sec
    lats = np.linspace(37.7749, 37.7849, num_points) # San Francisco area
    lons = np.linspace(-122.4194, -122.4094, num_points)
    
    gpx_template = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="MockGenerator" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>Mock Track</name>
    <trkseg>
{points}
    </trkseg>
  </trk>
</gpx>"""
    
    points_xml = ""
    for i in range(num_points):
        point_time = start_time + timedelta(seconds=i/points_per_sec)
        time_str = point_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        points_xml += f'      <trkpt lat="{lats[i]}" lon="{lons[i]}"><time>{time_str}</time></trkpt>\n'
        
    with open(output_gpx_path, 'w') as f:
        f.write(gpx_template.format(points=points_xml))
    
    print(f"Generated mock GPX: {output_gpx_path}")

def generate_mock_detections(output_csv_path, duration_sec=60):
    """
    Generates a mock detections.csv as if from detect.py.
    """
    data = []
    # Create 5-10 random detections
    for i in range(8):
        # Random timestamp within the video (0 to duration_sec)
        ts_ms = np.random.uniform(0, duration_sec * 1000)
        area = np.random.uniform(1000, 20000)
        severity = "Small"
        if area > 5000: severity = "Medium"
        if area > 15000: severity = "Large"
        
        data.append({
            'frame_id': int(ts_ms / 33), # ~30fps
            'timestamp_ms': round(ts_ms, 2),
            'pothole_id': i + 1,
            'confidence': round(np.random.uniform(0.6, 0.98), 2),
            'bbox_area': round(area, 2),
            'severity': severity
        })
    
    df = pd.DataFrame(data).sort_values('timestamp_ms')
    df.to_csv(output_csv_path, index=False)
    print(f"Generated mock detections: {output_csv_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate mock data for RoadScope AI testing")
    parser.add_argument("--output_dir", type=str, default="data/mock", help="Output directory")
    
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Use a fixed start time for syncing
    # Note: Use UTC for ISO 8601 compatibility
    start_time = datetime.utcnow().replace(microsecond=0)
    start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    gpx_path = os.path.join(args.output_dir, "test_track.gpx")
    detections_path = os.path.join(args.output_dir, "test_detections.csv")
    
    generate_mock_gps(gpx_path, start_time)
    generate_mock_detections(detections_path)
    
    print(f"\n🚀 Ready to test the pipeline!")
    print(f"Use these arguments:")
    print(f"  --video [any-video-path] --gpx {gpx_path} --start_time {start_time_str}")
    print(f"\nOr to test just the sync module:")
    print(f"  python src/mapping/sync_coords.py --detections {detections_path} --gpx_csv [parsed-gpx-csv] --start_time {start_time_str}")
