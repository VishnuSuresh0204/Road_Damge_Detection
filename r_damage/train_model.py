from ultralytics import YOLO

print("Starting YOLO training...")

# Load pretrained YOLO model
model = YOLO("yolo11n.pt")
    
# Train the model
results = model.train(
    data=r"E:\project26\Road_damege\Road-damage-3\data.yaml",       
    epochs=50,
    imgsz=640,
    batch=8,
    project=r"E:\project26\Road_damege\r_damage\runs",
    name="road_damage"
)

print("Training completed!")