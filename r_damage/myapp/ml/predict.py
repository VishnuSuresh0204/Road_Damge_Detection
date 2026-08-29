"""
YOLO-based road damage detection.

Loads a trained YOLO model (best.pt, trained on Pothole / Crack /
Surface Damage / Broken Road classes) and runs inference on an
uploaded road image.
"""
import os

import cv2
from ultralytics import YOLO

from .preprocessing import (
    get_image_dimensions,
    calculate_damage_area_percent,
    calculate_severity,
)

# Path to the trained weights file. Place best.pt in myapp/ml/
MODEL_PATH = os.path.join(os.path.dirname(__file__), "best.pt")
CONFIDENCE_THRESHOLD = 0.4

_model = None


def get_model():
    """
    Lazily load the YOLO model once and reuse it across requests
    instead of reloading it on every prediction call.
    """
    global _model
    if _model is None:
        _model = YOLO(MODEL_PATH)
    return _model


def run_inference(image_path):
    """
    Run YOLO inference on the given image and return a list of raw
    detections above the confidence threshold.

    Each detection dict contains:
        damage_type, confidence, x1, y1, x2, y2
    """
    model = get_model()
    results = model(image_path, conf=CONFIDENCE_THRESHOLD)

    detections = []
    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            class_name = model.names[class_id]
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]

            detections.append({
                "damage_type": class_name,
                "confidence": round(confidence * 100, 2),
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
            })

    return detections


def draw_boxes(image_path, detections, output_path):
    """
    Draw bounding boxes and labels on the image and save the
    annotated result to output_path.
    """
    image = cv2.imread(image_path)

    for det in detections:
        x1, y1, x2, y2 = int(det["x1"]), int(det["y1"]), int(det["x2"]), int(det["y2"])
        label = f"{det['damage_type']} {det['confidence']}%"

        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(
            image, label, (x1, max(y1 - 10, 10)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2
        )

    cv2.imwrite(output_path, image)
    return output_path


def pick_primary_detection(detections):
    """
    Choose the detection with the highest confidence to represent
    the overall damage_type/confidence stored on the report.
    """
    if not detections:
        return None
    return max(detections, key=lambda d: d["confidence"])


def detect_damage(image_path, output_path=None):
    """
    Full detection pipeline for a single uploaded image.

    Returns a dict:
        {
            "detections": [...],
            "primary": {...} or None,
            "damage_area_percent": float,
            "severity": "Low" | "Medium" | "High",
            "result_image_path": str or None,
        }
    """
    detections = run_inference(image_path)

    width, height = get_image_dimensions(image_path)
    damage_area_percent = calculate_damage_area_percent(detections, width, height)
    severity = calculate_severity(damage_area_percent, num_detections=len(detections))

    primary = pick_primary_detection(detections)

    result_image_path = None
    if detections and output_path:
        result_image_path = draw_boxes(image_path, detections, output_path)

    return {
        "detections": detections,
        "primary": primary,
        "damage_area_percent": damage_area_percent,
        "severity": severity,
        "result_image_path": result_image_path,
    }