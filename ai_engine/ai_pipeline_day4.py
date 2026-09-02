import os
import time
import cv2
import numpy as np
from shapely.geometry import Point, Polygon
from ultralytics import YOLO

# ----------------------------------------------------
# 1. CONFIGURATION
# ----------------------------------------------------
# Automatically resolves to your local media clip
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_SOURCE = os.path.join(BASE_DIR, "media", "WhatsApp Video 2026-08-29 at 11.14.59 PM.mp4")

# Set to 0 if you want to switch to your laptop webcam:
# VIDEO_SOURCE = 0

CONF_THRESHOLD = 0.30
MODEL_PATH = os.path.join(BASE_DIR, "yolov8n.pt")

# Target classes per build plan: person (0), car (2), truck (7), dog (16)
TARGET_CLASSES = {0: "person", 2: "car", 7: "truck", 16: "dog"}

# Tripwire zone defined in coordinate ratios (X%, Y%)
ZONE_COORDINATE_RATIOS = [
    (0.15, 0.40),  # Top-left
    (0.85, 0.40),  # Top-right
    (0.95, 0.90),  # Bottom-right
    (0.05, 0.90)   # Bottom-left
]

# ----------------------------------------------------
# 2. LOW-LIGHT ENHANCEMENT (DAY 3 MODULE)
# ----------------------------------------------------
def apply_clahe_enhancement(frame, brightness_threshold=90):
    """Applies bilateral smoothing + CLAHE on L-channel if dark."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)

    if mean_brightness < brightness_threshold:
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
# 3. PIPELINE LOOP
# ----------------------------------------------------
def run_pipeline():
    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(VIDEO_SOURCE)

    if not cap.isOpened():
        print(f"Error: Unable to open source: {VIDEO_SOURCE}")
        return

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Scale relative zone points to frame dimensions
    poly_points = [
        (int(x * frame_width), int(y * frame_height)) 
        for x, y in ZONE_COORDINATE_RATIOS
    ]
    tripwire_polygon = Polygon(poly_points)
    poly_np = np.array(poly_points, np.int32).reshape((-1, 1, 2))

    print("Pipeline running. Press 'q' on the video window to stop.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("End of video stream.")
            break

        # Step A: Low-light check & enhancement
        enhanced_frame, was_enhanced = apply_clahe_enhancement(frame)

        # Step B: ByteTrack tracking
        results = model.track(
            source=enhanced_frame,
            classes=list(TARGET_CLASSES.keys()),
            conf=CONF_THRESHOLD,
            imgsz=960,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False
        )

        # Draw tripwire polygon on display frame
        cv2.polylines(frame, [poly_np], isClosed=True, color=(0, 0, 255), thickness=2)
        cv2.putText(frame, "RESTRICTED PERIMETER ZONE", (poly_points[0][0], poly_points[0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Step C: Parse detections & check zone
        if results[0].boxes and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            confidences = results[0].boxes.conf.cpu().numpy()
            class_ids = results[0].boxes.cls.cpu().numpy().astype(int)
            track_ids = results[0].boxes.id.cpu().numpy().astype(int)

            for bbox, conf, cls_id, track_id in zip(boxes, confidences, class_ids, track_ids):
                x1, y1, x2, y2 = map(int, bbox)
                
                # Bottom-center is the ground/foot contact point
                bottom_center = Point(int((x1 + x2) / 2), y2)
                in_zone = tripwire_polygon.contains(bottom_center)

                # Day 5 JSON Contract format
                payload = {
                    "object_class": TARGET_CLASSES.get(cls_id, "unknown"),
                    "confidence": round(float(conf), 2),
                    "bbox": [x1, y1, x2, y2],
                    "track_id": int(track_id),
                    "in_zone": bool(in_zone),
                    "timestamp": int(time.time())
                }

                box_color = (0, 0, 255) if in_zone else (0, 255, 0)
                status_label = "INVASION" if in_zone else "OUTSIDE"

                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                cv2.circle(frame, (int((x1 + x2) / 2), y2), 4, (0, 0, 255), -1)

                cv2.putText(frame, f"ID:{track_id} {payload['object_class']} [{status_label}]",
                            (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)

                if in_zone:
                    print(f"[BREACH DETECTED] -> {payload}")

        status_text = "CLAHE: ACTIVE" if was_enhanced else "CLAHE: OFF"
        cv2.putText(frame, status_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        cv2.imshow("Sima-Drishti Surveillance Pipeline", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_pipeline()