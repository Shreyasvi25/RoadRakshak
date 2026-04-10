from fastapi import FastAPI, WebSocket
import cv2
import base64
import time

from detection import process_frame, detect_collisions

app = FastAPI()


# =========================
# HEALTH CHECK ROUTE
# =========================
@app.get("/")
def home():
    return {"message": "🚀 RoadGuard AI Server Running"}


# =========================
# NIGHT VISION FUNCTION
# =========================
def enhance_night_vision(frame):
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)

    limg = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    return enhanced


# =========================
# WEBSOCKET STREAM
# =========================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # =========================
        # SMART NIGHT VISION
        # =========================
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if gray.mean() < 80:  # low light condition
            frame = enhance_night_vision(frame)

        # =========================
        # DETECTION + COLLISION
        # =========================
        detections = process_frame(frame)
        collisions = detect_collisions(detections)

        print("Collision:", collisions)

        # =========================
        # DRAW DETECTIONS
        # =========================
        for obj in detections:
            x1, y1, x2, y2 = map(int, obj["bbox"])
            label = f"{obj['class']} {obj['confidence']:.2f}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # =========================
        # COLLISION ALERT
        # =========================
        if collisions:
            cv2.putText(frame, "🚨 COLLISION ALERT!", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

            # Save snapshot with timestamp
            filename = f"collision_{int(time.time())}.jpg"
            cv2.imwrite(filename, frame)

        # =========================
        # ENCODE FRAME
        # =========================
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = base64.b64encode(buffer).decode('utf-8')

        # =========================
        # SEND TO FRONTEND
        # =========================
        await websocket.send_json({
            "frame": frame_bytes,
            "collision": bool(collisions)
        })

    cap.release()