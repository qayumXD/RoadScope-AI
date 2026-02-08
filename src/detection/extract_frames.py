import cv2
import os
import argparse

def extract_frames(video_path, output_dir, interval_sec=1.0):
    """
    Extracts frames from a video file at a specified interval.
    
    Args:
        video_path (str): Path to the input video file.
        output_dir (str): Directory to save extracted images.
        interval_sec (float): Time interval in seconds between extracted frames.
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    if fps == 0:
        print("Error: Could not determine FPS. Is the video file valid?")
        return

    frame_interval = int(fps * interval_sec)
    frame_count = 0
    saved_count = 0

    print(f"Processing {video_path}...")
    print(f"FPS: {fps}, Extraction Interval: {interval_sec}s (every {frame_interval} frames)")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            frame_name = f"frame_{saved_count:04d}.jpg"
            output_path = os.path.join(output_dir, frame_name)
            cv2.imwrite(output_path, frame)
            saved_count += 1
            if saved_count % 10 == 0:
                print(f"Saved {saved_count} frames...", end='\r')

        frame_count += 1

    cap.release()
    print(f"\nDone! Extracted {saved_count} frames to '{output_dir}'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract frames from video for Pothole Dataset")
    parser.add_argument("--video", type=str, required=True, help="Path to input video file")
    parser.add_argument("--output", type=str, default="data/dataset/images", help="Output directory for images")
    parser.add_argument("--interval", type=float, default=1.0, help="Interval in seconds between frames (default: 1.0)")
    
    args = parser.parse_args()
    
    extract_frames(args.video, args.output, args.interval)
