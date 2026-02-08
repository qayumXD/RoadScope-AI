from ultralytics import YOLO
import argparse
import os

def train_yolo(data_yaml, epochs=50, img_size=640, batch_size=16, model_variant='yolov8n.pt'):
    """
    Trains a YOLOv8 model on a custom dataset.

    Args:
        data_yaml (str): Path to the dataset configuration file (data.yaml).
        epochs (int): Number of training epochs.
        img_size (int): Image size for training.
        batch_size (int): Batch size.
        model_variant (str): YOLOv8 model variant (n, s, m, l, x).
    """
    print(f"Starting training with model: {model_variant}")
    # Load a model
    model = YOLO(model_variant)  # load a pretrained model (recommended for training)

    # Train the model
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=img_size,
        batch=batch_size,
        name='pothole_model', # project name
        exist_ok=True, # overwrite existing experiment
    )
    
    # Evaluate the model's performance on the validation set
    metrics = model.val()
    print(f"Validation mAP50-95: {metrics.box.map}")

    # Export the model to ONNX format
    path = model.export(format="onnx")
    print(f"Model exported to {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLOv8 on Pothole Dataset")
    parser.add_argument("--data", type=str, required=True, help="Path to data.yaml file")
    parser.add_argument("--epochs", type=int, default=50, help="Number of epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="YOLOv8 model variant (default: yolov8n.pt)")

    args = parser.parse_args()

    train_yolo(args.data, args.epochs, args.imgsz, args.batch, args.model)
