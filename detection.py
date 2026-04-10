from ultralytics import YOLO

# Load model once (VERY IMPORTANT)
model = YOLO("yolov8n.pt")


def process_frame(frame):
    """
    Input: frame (image)
    Output: list of detections
    """

    results = model(frame)

    detections = []

    for r in results:
        boxes = r.boxes

        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])

            label = model.names[class_id]

            detections.append({
                "class": label,
                "confidence": confidence,
                "bbox": [x1, y1, x2, y2]
            })

    return detections
def calculate_iou(box1, box2):
    x1, y1, x2, y2 = box1
    x1b, y1b, x2b, y2b = box2

    xi1 = max(x1, x1b)
    yi1 = max(y1, y1b)
    xi2 = min(x2, x2b)
    yi2 = min(y2, y2b)

    inter_width = max(0, xi2 - xi1)
    inter_height = max(0, yi2 - yi1)
    intersection = inter_width * inter_height

    area1 = (x2 - x1) * (y2 - y1)
    area2 = (x2b - x1b) * (y2b - y1b)

    union = area1 + area2 - intersection

    if union == 0:
        return 0

    return intersection / union
def detect_collisions(detections):
    collisions = []

    vehicle_classes = ["car", "truck", "bus", "motorbike"]

    for i in range(len(detections)):
        for j in range(i + 1, len(detections)):

            obj1 = detections[i]
            obj2 = detections[j]

            if obj1["class"] in vehicle_classes and obj2["class"] in vehicle_classes:

                iou = calculate_iou(obj1["bbox"], obj2["bbox"])

                if iou > 0.3:  # threshold
                    collisions.append((obj1, obj2, iou))

    return collisions