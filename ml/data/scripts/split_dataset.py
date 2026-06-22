"""Split images and labels into train/val/test sets with YOLO directory structure."""

import argparse
import os
import random
import shutil
import sys
from typing import List


def get_image_files(directory: str) -> List[str]:
    """Return sorted list of image filenames in the directory."""
    extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    return sorted(
        name for name in os.listdir(directory)
        if os.path.splitext(name)[1].lower() in extensions
    )


def split_dataset(
    input_dir: str,
    output_dir: str,
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    seed: int = 42,
) -> None:
    """Split images (and labels if present) into train/val/test directories."""
    if not os.path.isdir(input_dir):
        print(f"Error: input directory not found: {input_dir}")
        sys.exit(1)

    total = train_ratio + val_ratio + test_ratio
    if abs(total - 1.0) > 0.01:
        print(f"Warning: ratios sum to {total:.2f}, normalizing to 1.0")
        train_ratio /= total
        val_ratio /= total
        test_ratio /= total

    image_files = get_image_files(input_dir)
    if not image_files:
        print(f"No image files found in {input_dir}")
        return

    random.seed(seed)
    random.shuffle(image_files)

    n = len(image_files)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    splits = {
        "train": image_files[:n_train],
        "val": image_files[n_train:n_train + n_val],
        "test": image_files[n_train + n_val:],
    }

    print(f"Total images: {n}")
    print(f"  train: {len(splits['train'])}, val: {len(splits['val'])}, test: {len(splits['test'])}")

    for split_name, files in splits.items():
        img_dir = os.path.join(output_dir, split_name, "images")
        lbl_dir = os.path.join(output_dir, split_name, "labels")
        os.makedirs(img_dir, exist_ok=True)
        os.makedirs(lbl_dir, exist_ok=True)

        for filename in files:
            src_img = os.path.join(input_dir, filename)
            dst_img = os.path.join(img_dir, filename)
            shutil.copy2(src_img, dst_img)

            label_name = os.path.splitext(filename)[0] + ".txt"
            src_label = os.path.join(input_dir, label_name)
            if os.path.isfile(src_label):
                dst_label = os.path.join(lbl_dir, label_name)
                shutil.copy2(src_label, dst_label)

    print(f"Done. Dataset split saved to {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split dataset into train/val/test sets.")
    parser.add_argument("--input", required=True, help="Directory containing images (and optional label .txt files)")
    parser.add_argument("--output", required=True, help="Output directory for the split dataset")
    parser.add_argument("--train", type=float, default=0.7, help="Training set ratio (default: 0.7)")
    parser.add_argument("--val", type=float, default=0.2, help="Validation set ratio (default: 0.2)")
    parser.add_argument("--test", type=float, default=0.1, help="Test set ratio (default: 0.1)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    args = parser.parse_args()

    split_dataset(args.input, args.output, args.train, args.val, args.test, args.seed)
