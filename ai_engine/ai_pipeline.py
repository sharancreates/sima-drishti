import os
import time
import queue
import threading
import base64
import requests
import cv2
import numpy as np
from shapely.geometry import Point, Polygon
from ultralytics import YOLO

# ----------------------------------------------------
# 1. CONFIGURATION
# ----------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_SOURCE = os.path.join(BASE_DIR, "media", "WhatsApp Video 2026-08-29 at 11.14.59 PM.mp4")
# VIDEO_SOURCE = 0  # Uncomment for live webcam

CONF_THRESHOLD = 0.35
MODEL_PATH = os.path.join(BASE_DIR, "yolov8n.pt")
BACKEND_ENDPOINT = "http://127.0.0.1:8000/detection"
API_KEY = os.getenv("API_KEY", "sima-drishti-secure-key-2026")

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
    """Consumes payloads from queue and dispatches to FastAPI with authentication."""
    session = requests.Session()
    api_key_header = {"X-API-Key": "sima-drishti-secure-key-2026"}
    session.headers.update(api_key_header)
    while True:
        payload = payload_queue.get()
        if payload is None:
            break
        try:
            response = session.post(BACKEND_ENDPOINT, json=payload, headers=api_key_header, timeout=1.0)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ALERT_CONFIRMED":
                    print(f"🚨 [ALERT CONFIRMED BY FUSION ENGINE] Alert ID: {data.get('alert_id')}")
            else:
                print(f"⚠️ [Backend Error {response.status_code}]: {response.text}")
        except requests.exceptions.RequestException:
            pass
        finally:
            payload_queue.task_done()

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

    print(f"AI Stream active. Broadcasting authenticated alerts to: {BACKEND_ENDPOINT}")

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

                # Generate base64 thumbnail crop for breach event
                frame_b64 = None
                if in_zone:
                    crop = frame[max(0, y1):min(frame_height, y2), max(0, x1):min(frame_width, x2)]
                    if crop.size > 0:
                        _, buffer = cv2.imencode('.jpg', crop)
                        frame_b64 = base64.b64encode(buffer).decode('utf-8')

                # Schema formatted to match Backend's DetectionPayload
                payload = {
                    "object_class": str(TARGET_CLASSES.get(cls_id, "unknown")),
                    "confidence": float(round(float(conf), 2)),
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "track_id": int(track_id),
                    "in_zone": bool(in_zone),
                    "zone_id": "ZONE_A",
                    "frame_image": frame_b64,
                    "timestamp": int(time.time())
                }

                payload_queue.put(payload)

                box_color = (0, 0, 255) if in_zone else (0, 255, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                cv2.putText(frame, f"ID:{track_id} {payload['object_class']} {'[BREACH]' if in_zone else ''}",
                            (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)

        status_text = "CLAHE: ACTIVE" if was_enhanced else "CLAHE: OFF"
        cv2.putText(frame, status_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        cv2.imshow("Sima-Drishti Surveillance Pipeline", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    payload_queue.put(None)

if __name__ == "__main__":
    run_pipeline()