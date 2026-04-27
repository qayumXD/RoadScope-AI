# RoadScope AI: Intelligent Pothole Detection and Mapping

RoadScope AI automates road inspection by detecting potholes from driving video, matching detections to GPS coordinates, and visualizing the results in a Next.js dashboard.

## Project Structure

```
RoadScope-AI/
├── data/
│   ├── dataset/             # YOLO training images and labels
│   ├── gps_logs/            # Raw GPX and parsed GPS CSV files
│   └── raw_videos/          # Input road videos
├── src/
│   ├── pipeline.py          # End-to-end orchestration script
│   ├── detection/
│   │   ├── extract_frames.py
│   │   ├── train.py
│   │   └── detect.py
│   ├── mapping/
│   │   ├── parse_gpx.py
│   │   ├── sync_coords.py
│   │   └── snap_to_road.py
│   └── dashboard/           # Next.js dashboard app
└── requirements.txt
```

## MVP Quick Start

### 1) Backend Setup (Python)

Prerequisites: Python 3.10+

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Run End-to-End Pipeline

```bash
python3 src/pipeline.py \
  --video data/raw_videos/road_trip.mp4 \
  --gpx data/gps_logs/road_trip.gpx \
  --start_time 2026-04-27T10:00:00Z \
  --model models/yolov8n.pt \
  --output_dir data/processed
```

Pipeline output:
- `data/processed/<video_name>_detections.csv`
- `data/processed/<video_name>_gps.csv`
- `data/processed/<video_name>_mapped_potholes.csv`
- Auto-published dashboard data: `src/dashboard/public/potholes.csv`

Optional road snapping:
- Add `--snap_key YOUR_GOOGLE_MAPS_API_KEY` to the pipeline command.

### 3) Start the Dashboard (Next.js)

Prerequisites: Node.js 18+

```bash
cd src/dashboard
npm install
cp env.local.example .env.local
```

Create `src/dashboard/.env.local` with:

```bash
NEXT_PUBLIC_GOOGLE_MAPS_KEY=your_google_maps_key
NEXT_PUBLIC_GOOGLE_MAPS_MAP_ID=
```

`NEXT_PUBLIC_GOOGLE_MAPS_MAP_ID` is optional.

Then run:

```bash
npm run dev
```

Open http://localhost:3000.

## Manual Workflow (Advanced)

If you prefer running each stage separately:
- `python3 src/detection/detect.py ...`
- `python3 src/mapping/parse_gpx.py ...`
- `python3 src/mapping/sync_coords.py ...`
- `python3 src/mapping/snap_to_road.py ...` (optional)

## Deployment Notes

- Frontend: deploy `src/dashboard` on Vercel.
- Detection/mapping jobs: run on a machine with enough CPU/GPU resources for YOLO inference.
