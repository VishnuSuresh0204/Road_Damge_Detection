import os
from ultralytics import YOLO
from django.conf import settings


MODEL_PATH = os.path.join(
    settings.BASE_DIR,
    "myapp",
    "ml",
    "best.pt"
)


# Load model only once
model = YOLO(MODEL_PATH)


def detect_road_damage(image_path):

    results = model(image_path, conf=0.25)

    result = results[0]

    detections = []

    for box in result.boxes:

        class_id = int(box.cls[0])
        confidence = float(box.conf[0])

        damage_type = result.names[class_id]

        detections.append({
            "damage_type": damage_type,
            "confidence": confidence,
        })

    # Save YOLO result image
    result_folder = os.path.join(
        settings.MEDIA_ROOT,
        "road_damage",
        "results"
    )

    os.makedirs(result_folder, exist_ok=True)

    image_name = os.path.basename(image_path)

    result_path = os.path.join(
        result_folder,
        f"detected_{image_name}"
    )

    result.save(filename=result_path)

    return detections, result_path