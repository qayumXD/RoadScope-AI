import argparse
import subprocess
import os
import sys

def run_step(command, description, cwd=None):
    print(f"\n>>> Step: {description}")
    print(f"Running: {' '.join(command)}")
    try:
        # Run the command and wait for it to finish
        result = subprocess.run(command, check=True, text=True, cwd=cwd)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error during {description}: {e}")
        return False
    except FileNotFoundError:
        print(f"Error: Command not found. Ensure Python is in your PATH and dependencies are installed.")
        return False

def main():
    parser = argparse.ArgumentParser(description="RoadScope AI: Full Pothole Mapping Pipeline")
    
    # Required Arguments
    parser.add_argument("--video", type=str, required=True, help="Path to input video (.mp4)")
    parser.add_argument("--gpx", type=str, required=True, help="Path to GPS log (.gpx)")
    parser.add_argument("--start_time", type=str, required=True, help="Video start time UTC (ISO 8601, e.g. 2023-10-27T14:30:00)")
    
    # Optional Arguments
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="YOLOv8 weights alias (e.g. yolov8n.pt) or path to local weights")
    parser.add_argument("--output_dir", type=str, default="data/processed", help="Directory for output files")
    parser.add_argument("--snap_key", type=str, help="Google Maps API Key (optional for snapping to roads)")

    args = parser.parse_args()

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def resolve_path(path_value):
        if os.path.isabs(path_value):
            return path_value
        return os.path.join(repo_root, path_value)

    def resolve_model_path(model_value):
        if os.path.isabs(model_value):
            return model_value

        has_path_separator = os.path.sep in model_value
        if os.path.altsep:
            has_path_separator = has_path_separator or (os.path.altsep in model_value)

        # A plain alias like "yolov8n.pt" should pass through so Ultralytics
        # can auto-download it if missing locally.
        if not has_path_separator:
            return model_value

        return os.path.join(repo_root, model_value)

    video_path = resolve_path(args.video)
    gpx_path = resolve_path(args.gpx)
    model_path = resolve_model_path(args.model)
    output_dir = resolve_path(args.output_dir)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    detections_csv = os.path.join(output_dir, f"{video_name}_detections.csv")
    gps_csv = os.path.join(output_dir, f"{video_name}_gps.csv")
    final_csv = os.path.join(output_dir, f"{video_name}_mapped_potholes.csv")

    # 1. Detection
    if not run_step([
        sys.executable, "src/detection/detect.py",
        "--video", video_path,
        "--model", model_path,
        "--output", detections_csv
    ], "Detecting Potholes in Video", cwd=repo_root):
        return

    # 2. Parse GPX
    if not run_step([
        sys.executable, "src/mapping/parse_gpx.py",
        "--gpx", gpx_path,
        "--output", gps_csv
    ], "Parsing GPX Data", cwd=repo_root):
        return

    # 3. Synchronize Coordinates
    if not run_step([
        sys.executable, "src/mapping/sync_coords.py",
        "--detections", detections_csv,
        "--gpx_csv", gps_csv,
        "--start_time", args.start_time,
        "--output", final_csv
    ], "Syncing Detections with GPS", cwd=repo_root):
        return

    # 4. Optional: Snap to Road
    if args.snap_key:
        snapped_csv = os.path.join(output_dir, f"{video_name}_snapped.csv")
        if not run_step([
            sys.executable, "src/mapping/snap_to_road.py",
            "--input", final_csv,
            "--output", snapped_csv,
            "--key", args.snap_key
        ], "Snapping Points to Road Network", cwd=repo_root):
            return
        final_csv = snapped_csv

    # 5. Publish to Dashboard
    import shutil
    dashboard_public = os.path.join(repo_root, "src", "dashboard", "public", "potholes.csv")
    try:
        os.makedirs(os.path.dirname(dashboard_public), exist_ok=True)
        shutil.copy2(final_csv, dashboard_public)
        print(f"\n📊 Published to Dashboard: {dashboard_public}")
    except Exception as e:
        print(f"Warning: Could not publish to dashboard: {e}")

    print("\n✅ All steps complete! Start the dashboard with 'npm run dev' in src/dashboard.")

if __name__ == "__main__":
    main()
