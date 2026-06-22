"""Extract frames from a video file at a specified FPS rate."""

import argparse
import os
import sys

import cv2


def extract_frames(input_path: str, output_dir: str, fps: float) -> int:
    """Extract frames from video at the given FPS and save as JPEG."""
    if not os.path.isfile(input_path):
        print(f"Error: video file not found: {input_path}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error: cannot open video: {input_path}")
        sys.exit(1)

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / video_fps if video_fps > 0 else 0

    print(f"Video: {input_path}")
    print(f"  FPS: {video_fps:.2f}, Total frames: {total_frames}, Duration: {duration:.1f}s")
    print(f"  Extracting at {fps} FPS")

    frame_interval = video_fps / fps if fps > 0 else 1
    saved_count = 0
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % max(1, int(round(frame_interval))) == 0:
            filename = f"frame_{saved_count:05d}.jpg"
            filepath = os.path.join(output_dir, filename)
            cv2.imwrite(filepath, frame)
            saved_count += 1

            if saved_count % 50 == 0:
                progress = (frame_idx / total_frames * 100) if total_frames > 0 else 0
                print(f"  Progress: {progress:.1f}% — saved {saved_count} frames")

        frame_idx += 1

    cap.release()
    print(f"Done. Extracted {saved_count} frames to {output_dir}")
    return saved_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract frames from a video file.")
    parser.add_argument("--input", required=True, help="Path to the input video file")
    parser.add_argument("--output", required=True, help="Directory to save extracted frames")
    parser.add_argument("--fps", type=float, default=2.0, help="Frames per second to extract (default: 2)")
    args = parser.parse_args()

    extract_frames(args.input, args.output, args.fps)
