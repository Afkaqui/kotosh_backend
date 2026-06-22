"""Apply data augmentations to a directory of images."""

import argparse
import os
import sys
from typing import List, Tuple

import cv2
import numpy as np


def horizontal_flip(image: np.ndarray) -> np.ndarray:
    """Flip image horizontally."""
    return cv2.flip(image, 1)


def rotate(image: np.ndarray, angle: float) -> np.ndarray:
    """Rotate image by the given angle in degrees, keeping the full image."""
    h, w = image.shape[:2]
    center = (w / 2, h / 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    cos = abs(matrix[0, 0])
    sin = abs(matrix[0, 1])
    new_w = int(h * sin + w * cos)
    new_h = int(h * cos + w * sin)

    matrix[0, 2] += (new_w - w) / 2
    matrix[1, 2] += (new_h - h) / 2

    return cv2.warpAffine(image, matrix, (new_w, new_h))


def adjust_brightness(image: np.ndarray, factor: float) -> np.ndarray:
    """Adjust brightness by a factor (1.0 = no change)."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] * factor, 0, 255)
    hsv = hsv.astype(np.uint8)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def get_image_files(directory: str) -> List[str]:
    """Return sorted list of image file paths in the directory."""
    extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    files = []
    for name in sorted(os.listdir(directory)):
        if os.path.splitext(name)[1].lower() in extensions:
            files.append(os.path.join(directory, name))
    return files


def augment_image(image_path: str, output_dir: str) -> List[str]:
    """Apply all augmentations to a single image and save results."""
    image = cv2.imread(image_path)
    if image is None:
        print(f"  Warning: cannot read {image_path}, skipping")
        return []

    base_name = os.path.splitext(os.path.basename(image_path))[0]
    ext = os.path.splitext(image_path)[1]
    saved: List[str] = []

    augmentations: List[Tuple[str, np.ndarray]] = [
        ("_flip", horizontal_flip(image)),
        ("_rot", rotate(image, np.random.choice([-15, 15]))),
        ("_bright", adjust_brightness(image, np.random.choice([0.8, 1.2]))),
    ]

    for suffix, aug_image in augmentations:
        out_name = f"{base_name}{suffix}{ext}"
        out_path = os.path.join(output_dir, out_name)
        cv2.imwrite(out_path, aug_image)
        saved.append(out_path)

    return saved


def augment_data(input_dir: str, output_dir: str) -> int:
    """Augment all images in input_dir and save to output_dir."""
    if not os.path.isdir(input_dir):
        print(f"Error: input directory not found: {input_dir}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    image_files = get_image_files(input_dir)
    if not image_files:
        print(f"No image files found in {input_dir}")
        return 0

    print(f"Found {len(image_files)} images in {input_dir}")
    total_saved = 0

    for i, img_path in enumerate(image_files, 1):
        saved = augment_image(img_path, output_dir)
        total_saved += len(saved)

        if i % 20 == 0 or i == len(image_files):
            print(f"  Processed {i}/{len(image_files)} images, {total_saved} augmented images saved")

    print(f"Done. Created {total_saved} augmented images in {output_dir}")
    return total_saved


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply augmentations to a directory of images.")
    parser.add_argument("--input", required=True, help="Directory containing source images")
    parser.add_argument("--output", required=True, help="Directory to save augmented images")
    args = parser.parse_args()

    augment_data(args.input, args.output)
