"""
Helper functions for the road damage detection pipeline: image
dimension lookup, damage area coverage, and severity classification.
"""
import cv2
import numpy as np


def get_image_dimensions(image_path):
    """
    Return (width, height) in pixels for the image at image_path.
    """
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image at {image_path}")

    height, width = image.shape[:2]
    return width, height


def calculate_damage_area_percent(detections, width, height):
    """
    Return the percentage (0-100) of the image area covered by the
    detected damage boxes.

    Boxes are unioned onto a single mask before measuring coverage,
    so overlapping detections aren't double-counted.
    """
    if not detections or width <= 0 or height <= 0:
        return 0.0

    mask = np.zeros((height, width), dtype=np.uint8)

    for det in detections:
        x1 = int(max(0, min(det["x1"], width)))
        y1 = int(max(0, min(det["y1"], height)))
        x2 = int(max(0, min(det["x2"], width)))
        y2 = int(max(0, min(det["y2"], height)))

        if x2 <= x1 or y2 <= y1:
            continue

        mask[y1:y2, x1:x2] = 1

    covered_pixels = int(mask.sum())
    total_pixels = width * height

    return round((covered_pixels / total_pixels) * 100, 2)


def calculate_severity(damage_area_percent, num_detections=0):
    """
    Classify overall severity from the area covered by damage and
    how many separate damage regions were detected.
    """
    if damage_area_percent >= 15 or num_detections >= 4:
        return "High"

    if damage_area_percent >= 5 or num_detections >= 2:
        return "Medium"

    return "Low"