#!/usr/bin/env python3
"""
image_locator_agent.py

Finds all image files inside a folder and outputs their full paths.
Optionally searches subfolders and writes results to a CSV file.
"""

import argparse
from pathlib import Path
import csv
from datetime import datetime

# Common image extensions
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"}


def find_images(folder: Path, recursive: bool = True):
    """Yield all image file paths in the folder (optionally recursive)."""
    if recursive:
        iterator = folder.rglob("*")
    else:
        iterator = folder.glob("*")

    for p in iterator:
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            yield p.resolve()


def save_to_csv(paths, output_path: Path):
    """Save image paths to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["image_name", "full_path"])
        for p in paths:
            writer.writerow([p.name, str(p)])


def main():
    parser = argparse.ArgumentParser(
        description="Find the address/location of all images in a folder."
    )
    parser.add_argument(
        "folder",
        type=str,
        help="Path to the folder containing images",
    )
    parser.add_argument(
        "-n", "--no-recursive",
        action="store_true",
        help="Do NOT search inside subfolders (default is recursive)",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="image_locations.csv",
        help="Output CSV file (default: image_locations.csv)",
    )

    args = parser.parse_args()

    folder = Path(args.folder).expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        print(f"Error: folder does not exist or is not a directory: {folder}")
        return

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scanning: {folder}")
    recursive = not args.no_recursive

    images = list(find_images(folder, recursive=recursive))

    if not images:
        print("No image files found.")
        return

    # Print results to console
    print(f"Found {len(images)} image(s):")
    for img in images:
        print(str(img))

    # Save to CSV
    output_path = Path(args.output).expanduser().resolve()
    save_to_csv(images, output_path)
    print(f"\nImage locations saved to: {output_path}")


if __name__ == "__main__":
    main()
