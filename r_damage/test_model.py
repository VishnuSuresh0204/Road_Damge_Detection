from ultralytics import YOLO

print("Loading model...")

# Load your trained model
model = YOLO(r"myapp\ml\best.pt")

print("Model loaded successfully!")

# Put the name of an image you want to test here
image_path = r"test.jpg"

# Detect road damage
results = model(image_path, conf=0.25)

# Show results
for result in results:
    result.show()

    # Print detected objects
    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])

        print(
            "Detected:",
            model.names[class_id],
            "| Confidence:",
            f"{confidence:.2%}"
        )