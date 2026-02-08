from ultralytics import YOLO
import cv2
import csv
import os
import argparse
import time

def detect_potholes(video_path, model_path, output_csv, show_video=False):
    """
    Runs inference on a video and saves detections to a CSV file.
    
    Args:
        video_path (str): Path to input video.
        model_path (str): Path to trained YOLOv8 model weights (.pt).
        output_csv (str): Path to save detection results.
        show_video (bool): Whether to display the video during inference.
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    # Load the model
    print(f"Loading model from {model_path}...")
    model = YOLO(model_path)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Prepare CSV file
    # We will log: frame_id, timestamp_ms, class_id, confidence, bbox(xywh), severity_label
    with open(output_csv, 'w', newline='') as csvfile:
        fieldnames = ['frame_id', 'timestamp_ms', 'pothole_id', 'confidence', 'bbox_area', 'severity']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        frame_id = 0
        pothole_count = 0

        print(f"Processing {video_path}...")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Timestamp in milliseconds
            timestamp_ms = cap.get(cv2.CAP_PROP_POS_MSEC)

            # Run inference
            results = model.predict(frame, conf=0.25, verbose=False) # Adjust conf threshold as needed
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Bounding box
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    w = x2 - x1
                    h = y2 - y1
                    area = w * h
                    
                    # Confidence
                    conf = float(box.conf[0])
                    
                    # Class ID (assuming 0 is pothole)
                    cls = int(box.cls[0])
                    
                    # Simple Severity Logic (Customize thresholds based on camera/resolution)
                    severity = "Small"
                    if area > 5000: # Example threshold
                        severity = "Medium"
                    if area > 15000:
                        severity = "Large"

                    # ID for this detection (simplified, not tracking across frames yet)
                    pothole_count += 1
                    
                    # Write to CSV
                    writer.writerow({
                        'frame_id': frame_id,
                        'timestamp_ms': f"{timestamp_ms:.2f}",
                        'pothole_id': pothole_count,
                        'confidence': f"{conf:.2f}",
                        'bbox_area': f"{area:.2f}",
                        'severity': severity
                    })

            # Visualization (Slows down processing)
            if show_video:
                annotated_frame = results[0].plot()
                cv2.imshow("Pothole Detection", annotated_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            frame_id += 1
            if frame_id % 100 == 0:
                print(f"Processed {frame_id} frames...", end='\r')

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nInference complete. Results saved to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run YOLOv8 Inference on Video")
    parser.add_argument("--video", type=str, required=True, help="Path to input video")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="Path to model weights")
    parser.add_argument("--output", type=str, default="detections.csv", help="Path to output CSV")
    parser.add_argument("--show", action="store_true", help="Show video during processing")

    args = parser.parse_args()
    
    detect_potholes(args.video, args.model, args.output, args.show)
