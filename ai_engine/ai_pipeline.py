import os
import time
import queue
import threading
import requests
import cv2
import numpy as np
from shapely.geometry import Point, Polygon
from ultralytics import YOLO

# ----------------------------------------------------
# 1. CONFIGURATION
# ----------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_SOURCE = os.path.join(BASE_DIR, "media", "WhatsApp Video 2026-09-01 at 8.10.04 PM.mp4")
# VIDEO_SOURCE = 0  # Uncomment for live webcam

CONF_THRESHOLD = 0.30
MODEL_PATH = os.path.join(BASE_DIR, "yolov8n.pt")
BACKEND_ENDPOINT = "http://127.0.0.1:8000/detection"

TARGET_CLASSES = {0: "person", 2: "car", 7: "truck", 16: "dog"}

ZONE_COORDINATE_RATIOS = [
    (0.15, 0.40),
    (0.85, 0.40),
    (0.95, 0.90),
    (0.05, 0.90)
]

# ----------------------------------------------------
# 2. ASYNC BACKGROUND HTTP DISPATCHER
# ----------------------------------------------------
payload_queue = queue.Queue()

def backend_sender_worker():
    """Consumes payloads from queue and dispatches to FastAPI asynchronously."""
    session = requests.Session()
    while True:
        payload = payload_queue.get()
        if payload is None:
            break
        try:
            response = session.post(BACKEND_ENDPOINT, json=payload, timeout=1.0)
            if response.status_code not in (200, 201):
                print(f"⚠️ [Backend Error {response.status_code}]: {response.text}")
        except requests.exceptions.RequestException:
            # Avoid crashing if the backend service isn't turned on yet
            pass
        finally:
            payload_queue.task_done()

# Start background network thread
network_thread = threading.Thread(target=backend_sender_worker, daemon=True)
network_thread.start()

# ----------------------------------------------------
# 3. LOW-LIGHT MODULE
# ----------------------------------------------------
def apply_clahe_enhancement(frame, brightness_threshold=90):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if np.mean(gray) < brightness_threshold:
        smooth = cv2.bilateralFilter(frame, d=5, sigmaColor=35, sigmaSpace=35)
        lab = cv2.cvtColor(smooth, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=1.8, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)
        inv_gamma = 1.0 / 1.25
        lut = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(256)]).astype("uint8")
        l_enhanced = cv2.LUT(l_enhanced, lut)
        merged = cv2.merge((l_enhanced, a, b))
        return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR), True
    return frame, False

# ----------------------------------------------------
# 4. MAIN PIPELINE
# ----------------------------------------------------
def run_pipeline():
    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(VIDEO_SOURCE)

    if not cap.isOpened():
        print(f"Error: Unable to open source: {VIDEO_SOURCE}")
        return

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    poly_points = [
        (int(x * frame_width), int(y * frame_height)) 
        for x, y in ZONE_COORDINATE_RATIOS
    ]
    tripwire_polygon = Polygon(poly_points)
    poly_np = np.array(poly_points, np.int32).reshape((-1, 1, 2))

    print(f"AI Stream active. Broadcasting alerts to: {BACKEND_ENDPOINT}")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        enhanced_frame, was_enhanced = apply_clahe_enhancement(frame)

        results = model.track(
            source=enhanced_frame,
            classes=list(TARGET_CLASSES.keys()),
            conf=CONF_THRESHOLD,
            imgsz=960,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False
        )

        cv2.polylines(frame, [poly_np], isClosed=True, color=(0, 0, 255), thickness=2)

        if results[0].boxes and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            confidences = results[0].boxes.conf.cpu().numpy()
            class_ids = results[0].boxes.cls.cpu().numpy().astype(int)
            track_ids = results[0].boxes.id.cpu().numpy().astype(int)

            for bbox, conf, cls_id, track_id in zip(boxes, confidences, class_ids, track_ids):
                x1, y1, x2, y2 = map(int, bbox)
                bottom_center = Point(int((x1 + x2) / 2), y2)
                in_zone = tripwire_polygon.contains(bottom_center)

                # Explicitly cast to native Python types to satisfy FastAPI Pydantic schemas
                payload = {
                    "object_class": str(TARGET_CLASSES.get(cls_id, "unknown")),
                    "confidence": float(round(float(conf), 2)),
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "track_id": int(track_id),
                    "in_zone": bool(in_zone),
                    "timestamp": int(time.time())
                }

                # Push to worker queue without dropping video frame rates
                payload_queue.put(payload)

                box_color = (0, 0, 255) if in_zone else (0, 255, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                cv2.putText(frame, f"ID:{track_id} {payload['object_class']} {'[BREACH]' if in_zone else ''}",
                            (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)

        cv2.imshow("Sima-Drishti Surveillance Pipeline", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    payload_queue.put(None)  # stop worker

if __name__ == "__main__":
    run_pipeline()