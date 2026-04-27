from ultralytics import YOLO
import argparse
import os
import shutil
from pathlib import Path

def train_yolo(
    data_yaml,
    epochs=50,
    img_size=640,
    batch_size=16,
    model_variant='yolov8n.pt',
    output_model='models/pothole_yolov8n.pt',
    project='runs/train',
    run_name='pothole_model'
):
    """
    Trains a YOLOv8 model on a custom dataset.

    Args:
        data_yaml (str): Path to the dataset configuration file (data.yaml).
        epochs (int): Number of training epochs.
        img_size (int): Image size for training.
        batch_size (int): Batch size.
        model_variant (str): YOLOv8 model variant (n, s, m, l, x).
        output_model (str): Path where the trained .pt model will be copied.
        project (str): Directory where Ultralytics training artifacts are stored.
        run_name (str): Ultralytics run name.
    """
    repo_root = Path(__file__).resolve().parents[2]

    data_yaml_path = Path(data_yaml)
    if not data_yaml_path.is_absolute():
        data_yaml_path = repo_root / data_yaml_path

    output_model_path = Path(output_model)
    if not output_model_path.is_absolute():
        output_model_path = repo_root / output_model_path

    project_path = Path(project)
    if not project_path.is_absolute():
        project_path = repo_root / project_path

    if not data_yaml_path.exists():
        raise FileNotFoundError(f"data.yaml not found at: {data_yaml_path}")

    print(f"Starting training with model: {model_variant}")
    # Load a model
    model = YOLO(model_variant)  # load a pretrained model (recommended for training)

    # Train the model
    results = model.train(
        data=str(data_yaml_path),
        epochs=epochs,
        imgsz=img_size,
        batch=batch_size,
        project=str(project_path),
        name=run_name,
        exist_ok=True, # overwrite existing experiment
    )

    run_dir = Path(results.save_dir)
    best_weights = run_dir / 'weights' / 'best.pt'
    last_weights = run_dir / 'weights' / 'last.pt'
    source_weights = best_weights if best_weights.exists() else last_weights

    if not source_weights.exists():
        raise FileNotFoundError(f"No trained weights found in: {run_dir / 'weights'}")

    output_model_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_weights, output_model_path)
    print(f"Saved trained model to {output_model_path}")
    
    # Evaluate the model's performance on the validation set
    trained_model = YOLO(str(output_model_path))
    metrics = trained_model.val(data=str(data_yaml_path))
    print(f"Validation mAP50-95: {metrics.box.map}")

    # Export the model to ONNX format and keep a stable copy next to the .pt file.
    onnx_exported_path = Path(trained_model.export(format="onnx", imgsz=img_size))
    stable_onnx_path = output_model_path.with_suffix('.onnx')
    if onnx_exported_path.resolve() != stable_onnx_path.resolve():
        shutil.copy2(onnx_exported_path, stable_onnx_path)
    print(f"Model exported to {stable_onnx_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLOv8 on Pothole Dataset")
    parser.add_argument("--data", type=str, required=True, help="Path to data.yaml file")
    parser.add_argument("--epochs", type=int, default=50, help="Number of epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="YOLOv8 model variant (default: yolov8n.pt)")
    parser.add_argument("--output_model", type=str, default="models/pothole_yolov8n.pt", help="Path to save trained .pt model")
    parser.add_argument("--project", type=str, default="runs/train", help="Directory for Ultralytics training artifacts")
    parser.add_argument("--name", type=str, default="pothole_model", help="Training run name")

    args = parser.parse_args()

    train_yolo(
        args.data,
        args.epochs,
        args.imgsz,
        args.batch,
        args.model,
        args.output_model,
        args.project,
        args.name,
    )
