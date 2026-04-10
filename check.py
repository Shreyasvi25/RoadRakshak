from ultralytics import YOLO
import cv2

# Load YOLO model
model = YOLO("yolov8n.pt")  # lightweight model

# Open webcam (0 = default camera)
cap = cv2.VideoCapture(0)

# while True:
#     ret, frame = cap.read()

#     if not ret:
#         break

#     # Run detection
#     results = model(frame)

#     # Draw results on frame
#     annotated_frame = results[0].plot()

#     # Show output
#     cv2.imshow("YOLO Detection", annotated_frame)

#     # Press 'q' to quit
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()
import cv2
from detection import process_frame, detect_collisions

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    if not ret:
        break

    detections = process_frame(frame)

    collisions = detect_collisions(detections)

    # Print collisions
    if collisions:
        print("🚨 COLLISION DETECTED:", collisions)

    cv2.imshow("Frame", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()