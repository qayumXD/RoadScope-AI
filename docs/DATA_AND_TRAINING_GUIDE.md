# RoadScope Data and Training Guide

This guide explains how to get pothole data, prepare it for YOLO, and train a detector when your laptop has no GPU.

## Current Project Status

- The detector training entrypoint is in `src/detection/train.py`.
- The full pipeline uses `--model` in `src/pipeline.py`.
- The repository currently does not include labeled training data in `data/dataset`.

## Recommended Plan for Your Laptop (i7 10th gen, 16GB RAM)

1. Do data prep and annotation locally.
2. Run a short local CPU smoke training (`1-3` epochs) to validate labels and config.
3. Run full training on free cloud GPU resources (Kaggle first, Colab second).
4. Bring back `best.pt` as `models/pothole_yolov8n.pt`.
5. Run local inference and pipeline with that model.

You can train on CPU locally, but full training will be slow. For MVP speed, use cloud GPU for the long run.

## 1) How to Get Data

### Option A: Collect Your Own Data (Best for your road conditions)

1. Record road video from a fixed camera angle (dashcam style).
2. Log GPX at the same time using phone GPS logging.
3. Keep notes of video start time in UTC for sync.
4. Extract candidate frames:

```bash
python3 src/detection/extract_frames.py \
  --video data/raw_videos/road_trip.mp4 \
  --output data/dataset/images/raw \
  --interval 0.5
```

5. Label potholes in extracted images.

### Option B: Use Public Datasets (Fast bootstrap)

Use public road-damage or pothole datasets from Kaggle, Hugging Face Datasets, or academic challenge sets.

Practical search terms:
- `pothole detection yolo`
- `road damage dataset`
- `RDD2022 pothole`

Example Kaggle CLI flow:

```bash
kaggle datasets list -s "pothole yolo"
kaggle datasets download -d <owner/dataset-slug> -p data/raw_public --unzip
```

Notes:
- Some datasets include multiple classes. Keep only pothole for class `0` unless you want multi-class training.
- Some labels are not YOLO format and must be converted.

## 2) Labeling Standard (YOLO)

Each label file (same base name as image) should have lines:

```text
<class_id> <x_center> <y_center> <width> <height>
```

All coordinates must be normalized to `0-1`.

For this project:
- `class_id = 0` means `pothole`

Recommended tools:
- CVAT
- Roboflow
- Label Studio
- LabelImg (YOLO mode)

## 3) Dataset Folder Layout

Your final dataset should look like this:

```text
data/dataset/
  images/
    train/
    val/
  labels/
    train/
    val/
```

Your existing config in `data/data.yaml` already expects this structure.

## 4) Data Quality Checklist

Before training, verify:

1. Every training image has a matching `.txt` label file (unless intentionally empty).
2. Label boxes are tight around potholes.
3. Day/night, dry/wet, and different road textures are represented.
4. Validation split is from different road segments than train split.
5. No duplicate near-identical frames dominate one split.

## 5) Local CPU Smoke Training (Do this first)

Before training, run the dataset validator:

```bash
python3 src/utils/validate_dataset.py --data data/data.yaml
```

Strict mode (recommended before long cloud training):

```bash
python3 src/utils/validate_dataset.py --data data/data.yaml --strict
```

`src/detection/train.py` runs this validation preflight by default.
Use `--skip_validate` only for debugging quick experiments.

Run a short validation training to catch bad labels/config quickly:

```bash
python3 src/detection/train.py \
  --data data/data.yaml \
  --model yolov8n.pt \
  --epochs 3 \
  --imgsz 640 \
  --batch 4 \
  --output_model models/pothole_yolov8n_smoke.pt
```

If this fails or is too slow, fix data issues before a longer run.

## 6) Full Training Without Local GPU

## 6A) Kaggle (Recommended first)

Why:
- Usually stable notebook environment for free GPU sessions.
- Good for repeated experiments.

High-level workflow:

1. Create a Kaggle Notebook with GPU enabled.
2. Add your dataset (upload or attach as Kaggle Dataset).
3. Clone this repo in notebook.
4. Install dependencies.
5. Train and save model in `/kaggle/working`.
6. Download artifact.

Example notebook commands:

```bash
!git clone <your-repo-url>
%cd RoadScope-AI
!pip install -r requirements.txt
!python src/detection/train.py \
  --data data/data.yaml \
  --model yolov8n.pt \
  --epochs 50 \
  --imgsz 640 \
  --batch 16 \
  --output_model /kaggle/working/pothole_yolov8n.pt
```

Then download `/kaggle/working/pothole_yolov8n.pt`.

## 6B) Google Colab (Great fallback)

Why:
- Easy to start quickly.
- Good for one-off full training runs.

High-level workflow:

1. Runtime -> GPU.
2. Clone repo.
3. Mount Google Drive.
4. Put dataset under Drive or upload directly.
5. Train and save to Drive.

Example:

```bash
!git clone <your-repo-url>
%cd RoadScope-AI
!pip install -r requirements.txt
!python src/detection/train.py \
  --data data/data.yaml \
  --model yolov8n.pt \
  --epochs 50 \
  --imgsz 640 \
  --batch 16 \
  --output_model /content/drive/MyDrive/RoadScope/models/pothole_yolov8n.pt
```

## 6C) Hugging Face (Useful, but not first choice for free long training)

Best uses:
- Host datasets.
- Share trained model artifacts.
- Deploy inference demo (Spaces).

For free full training, Kaggle and Colab are usually simpler and more consistent.

## 7) Bring Trained Model Back to This Repo

From your laptop in project root:

```bash
mkdir -p models
cp <downloaded-path>/pothole_yolov8n.pt models/pothole_yolov8n.pt
```

Run pipeline with your trained model:

```bash
python3 src/pipeline.py \
  --video data/raw_videos/road_trip.mp4 \
  --gpx data/gps_logs/road_trip.gpx \
  --start_time 2026-04-27T10:00:00Z \
  --model models/pothole_yolov8n.pt \
  --output_dir data/processed
```

## 8) Should You Train on This Laptop?

Short answer: yes for small smoke runs, no for full experiments if you want speed.

Good local use cases:
- `1-3` epoch smoke tests
- quick hyperparameter sanity checks
- small subset experiments

Move to cloud GPU when:
- training takes too long on CPU
- you need `30-100` epochs
- dataset size grows beyond quick iteration

## 9) Practical MVP Strategy

1. Build/clean dataset locally.
2. Run `3` epoch local smoke training.
3. Run `50` epoch Kaggle or Colab training.
4. Evaluate on your own holdout road clips.
5. Keep best model as `models/pothole_yolov8n.pt`.
6. Iterate labels first, hyperparameters second.
