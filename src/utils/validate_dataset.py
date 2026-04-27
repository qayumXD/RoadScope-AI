import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import yaml

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@dataclass
class SplitStats:
    name: str
    images: int = 0
    labels_found: int = 0
    missing_labels: int = 0
    empty_labels: int = 0
    invalid_label_lines: int = 0
    missing_images: int = 0
    orphan_labels: int = 0


def _resolve_path(base_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _split_sources(dataset_root: Path, split_value: object) -> List[Path]:
    if split_value in (None, ""):
        return []

    values: List[str]
    if isinstance(split_value, str):
        values = [split_value]
    elif isinstance(split_value, list):
        values = [str(item) for item in split_value if item not in (None, "")]
    else:
        raise TypeError(f"Unsupported split value type: {type(split_value)!r}")

    return [_resolve_path(dataset_root, item) for item in values]


def _collect_images(source: Path) -> List[Path]:
    if source.is_file() and source.suffix.lower() == ".txt":
        images: List[Path] = []
        with source.open("r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                images.append(_resolve_path(source.parent, line))
        return images

    if source.is_file() and source.suffix.lower() in IMAGE_EXTENSIONS:
        return [source]

    if source.is_dir():
        return sorted(path for path in source.rglob("*") if path.suffix.lower() in IMAGE_EXTENSIONS)

    return []


def _swap_segment(path: Path, source_segment: str, target_segment: str) -> Optional[Path]:
    parts = list(path.parts)
    if source_segment not in parts:
        return None
    index = parts.index(source_segment)
    parts[index] = target_segment
    return Path(*parts)


def _label_path_for_image(image_path: Path) -> Path:
    labels_path = _swap_segment(image_path, "images", "labels")
    if labels_path is None:
        return image_path.with_suffix(".txt")
    return labels_path.with_suffix(".txt")


def _image_exists_for_label(label_path: Path) -> bool:
    candidate = _swap_segment(label_path, "labels", "images")
    if candidate is None:
        candidate = label_path
    candidate = candidate.with_suffix("")

    for file_path in candidate.parent.glob(f"{candidate.name}.*"):
        if file_path.suffix.lower() in IMAGE_EXTENSIONS:
            return True
    return False


def _validate_label_file(label_path: Path, num_classes: int) -> Tuple[int, bool]:
    invalid_lines = 0
    non_empty_lines = 0

    with label_path.open("r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line:
                continue

            non_empty_lines += 1
            tokens = line.split()
            if len(tokens) != 5:
                invalid_lines += 1
                continue

            try:
                class_id = int(tokens[0])
                x_center, y_center, width, height = (float(value) for value in tokens[1:])
            except ValueError:
                invalid_lines += 1
                continue

            if class_id < 0 or class_id >= num_classes:
                invalid_lines += 1
                continue

            coords = (x_center, y_center, width, height)
            if any(value < 0.0 or value > 1.0 for value in coords):
                invalid_lines += 1
                continue

            if width <= 0.0 or height <= 0.0:
                invalid_lines += 1

    is_empty = non_empty_lines == 0
    return invalid_lines, is_empty


def validate_dataset(data_yaml: Path, strict: bool = False) -> bool:
    with data_yaml.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    if not isinstance(config, dict):
        print("Error: data config must be a YAML mapping.", file=sys.stderr)
        return False

    if "path" not in config:
        print("Error: data config must include 'path'.", file=sys.stderr)
        return False

    names = config.get("names")
    if isinstance(names, dict):
        num_classes = len(names)
    elif isinstance(names, list):
        num_classes = len(names)
    else:
        print("Error: data config must include 'names' as a list or dict.", file=sys.stderr)
        return False

    if num_classes == 0:
        print("Error: class list in 'names' is empty.", file=sys.stderr)
        return False

    dataset_root = _resolve_path(data_yaml.parent, str(config["path"]))
    if not dataset_root.exists():
        print(f"Error: dataset root does not exist: {dataset_root}", file=sys.stderr)
        return False

    print(f"Validating dataset using {data_yaml}")
    print(f"Resolved dataset root: {dataset_root}")
    print(f"Detected classes: {num_classes}")

    errors: List[str] = []
    warnings: List[str] = []
    split_reports: List[SplitStats] = []

    for split_name in ("train", "val", "test"):
        split_value = config.get(split_name)
        if split_name == "test" and split_value in (None, ""):
            continue

        try:
            sources = _split_sources(dataset_root, split_value)
        except TypeError as exc:
            errors.append(f"{split_name}: {exc}")
            continue

        if not sources and split_name in {"train", "val"}:
            errors.append(f"{split_name}: no source configured in data YAML")
            continue

        report = SplitStats(name=split_name)
        seen_images = set()

        for source in sources:
            if not source.exists():
                errors.append(f"{split_name}: source does not exist -> {source}")
                continue

            images = _collect_images(source)
            if not images:
                warnings.append(f"{split_name}: no images discovered in source -> {source}")

            for image_path in images:
                image_key = str(image_path.resolve())
                if image_key in seen_images:
                    continue
                seen_images.add(image_key)

                if not image_path.exists():
                    report.missing_images += 1
                    continue

                report.images += 1
                label_path = _label_path_for_image(image_path)

                if not label_path.exists():
                    report.missing_labels += 1
                    continue

                report.labels_found += 1
                invalid_count, is_empty = _validate_label_file(label_path, num_classes)
                report.invalid_label_lines += invalid_count
                if is_empty:
                    report.empty_labels += 1

            if source.is_dir():
                labels_dir = _swap_segment(source, "images", "labels")
                if labels_dir and labels_dir.exists():
                    for label_path in labels_dir.rglob("*.txt"):
                        if not _image_exists_for_label(label_path):
                            report.orphan_labels += 1

        if split_name in {"train", "val"} and report.images == 0:
            errors.append(f"{split_name}: no images found")

        if report.missing_images > 0:
            errors.append(f"{split_name}: {report.missing_images} image paths do not exist")

        if report.invalid_label_lines > 0:
            errors.append(f"{split_name}: {report.invalid_label_lines} invalid label lines found")

        if report.missing_labels > 0:
            message = f"{split_name}: {report.missing_labels} images missing label files"
            if strict:
                errors.append(message)
            else:
                warnings.append(message)

        if report.orphan_labels > 0:
            message = f"{split_name}: {report.orphan_labels} label files have no matching images"
            if strict:
                errors.append(message)
            else:
                warnings.append(message)

        split_reports.append(report)

    print("\nSplit summary:")
    for report in split_reports:
        print(
            f"- {report.name}: images={report.images}, labels={report.labels_found}, "
            f"missing_labels={report.missing_labels}, empty_labels={report.empty_labels}, "
            f"invalid_label_lines={report.invalid_label_lines}, orphan_labels={report.orphan_labels}"
        )

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"- {warning}")

    if errors:
        print("\nErrors:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return False

    print("\nDataset validation passed.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate YOLO dataset integrity for RoadScope training")
    parser.add_argument("--data", type=str, required=True, help="Path to data.yaml")
    parser.add_argument("--strict", action="store_true", help="Treat missing labels and orphan labels as errors")

    args = parser.parse_args()

    data_yaml_path = Path(args.data).resolve()
    if not data_yaml_path.exists():
        print(f"Error: data YAML not found -> {data_yaml_path}", file=sys.stderr)
        sys.exit(1)

    ok = validate_dataset(data_yaml_path, strict=args.strict)
    sys.exit(0 if ok else 1)
