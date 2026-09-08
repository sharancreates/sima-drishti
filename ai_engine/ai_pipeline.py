import os
import sys
import time
import queue
import threading
import argparse
import base64
import requests
import cv2
import numpy as np
from shapely.geometry import Point, Polygon
from ultralytics import YOLO

# ----------------------------------------------------
# 1. CONFIGURATION & VIDEO PRESETS
# ----------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "media")

VIDEO_PRESETS = {
    "1": os.path.join(MEDIA_DIR, "WhatsApp Video 2026-08-29 at 11.14.59 PM.mp4"),
    "person": os.path.join(MEDIA_DIR, "WhatsApp Video 2026-08-29 at 11.14.59 PM.mp4"),
    "breach": os.path.join(MEDIA_DIR, "WhatsApp Video 2026-08-29 at 11.14.59 PM.mp4"),

    "2": os.path.join(MEDIA_DIR, "Stray_dog_crosses_border_fence_202608292240.mp4"),
    "dog": os.path.join(MEDIA_DIR, "Stray_dog_crosses_border_fence_202608292240.mp4"),
    "animal": os.path.join(MEDIA_DIR, "Stray_dog_crosses_border_fence_202608292240.mp4"),

    "3": os.path.join(MEDIA_DIR, "WhatsApp Video 2026-09-01 at 8.10.04 PM.mp4"),
    "fence": os.path.join(MEDIA_DIR, "WhatsApp Video 2026-09-01 at 8.10.04 PM.mp4"),
    "river": os.path.join(MEDIA_DIR, "WhatsApp Video 2026-09-01 at 8.10.04 PM.mp4"),

    "0": 0,
    "webcam": 0
}

def resolve_video_source(source_arg):
    s = str(source_arg).strip().lower()
    if s in VIDEO_PRESETS:
        return VIDEO_PRESETS[s]
    if s.isdigit():
        return int(s)
    if os.path.exists(source_arg):
        return source_arg
    in_media = os.path.join(MEDIA_DIR, source_arg)
    if os.path.exists(in_media):
        return in_media
    print(f"Warning: Video source '{source_arg}' not found, defaulting to Breach Video Preset (1).")
    return VIDEO_PRESETS["1"]

MODEL_PATH = os.path.join(BASE_DIR, "yolov8n.pt")
BACKEND_ENDPOINT = "http://127.0.0.1:8000/detection"
API_KEY = os.getenv("API_KEY", "sima-drishti-secure-key-2026")
STREAM_ENDPOINT = os.getenv("STREAM_ENDPOINT", "http://127.0.0.1:8000/stream/frame")

TARGET_CLASSES = {0: "person", 2: "car", 7: "truck", 16: "dog"}

ZONE_COORDINATE_RATIOS = [
    (0.15, 0.40),
    (0.85, 0.40),
    (0.95, 0.90),
    (0.05, 0.90)
]

# ----------------------------------------------------
# 2. ASYNC BACKGROUND HTTP DISPATCHER & STREAMER
# ----------------------------------------------------
payload_queue = queue.Queue()
frame_stream_queue = queue.Queue(maxsize=8)
CURRENT_CAMERA_ID = "cam-04"

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

def frame_stream_worker():
    """Streams compressed JPEG frames to FastAPI MJPEG endpoint for web app rendering."""
    session = requests.Session()
    while True:
        item = frame_stream_queue.get()
        if item is None:
            break
        if isinstance(item, tuple):
            cam_id, frame_bytes = item
        else:
            cam_id, frame_bytes = CURRENT_CAMERA_ID, item
        try:
            headers = {
                "Content-Type": "image/jpeg",
                "X-Camera-ID": cam_id
            }
            session.post(f"{STREAM_ENDPOINT}?cam_id={cam_id}", data=frame_bytes, headers=headers, timeout=0.5)
        except Exception:
            pass
        finally:
            frame_stream_queue.task_done()

network_thread = threading.Thread(target=backend_sender_worker, daemon=True)
network_thread.start()

stream_thread = threading.Thread(target=frame_stream_worker, daemon=True)
stream_thread.start()

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
def run_pipeline(source="1", camera_id="cam-04", conf_threshold=0.35, imgsz=640):
    global CURRENT_CAMERA_ID
    CURRENT_CAMERA_ID = camera_id

    resolved_source = resolve_video_source(source)
    source_name = resolved_source if isinstance(resolved_source, str) else "Webcam (Device 0)"

    print("==================================================")
    print("   SIMA-DRISHTI AI EDGE SURVEILLANCE PIPELINE   ")
    print("==================================================")
    print(f"Target Camera Channel: {camera_id.upper()}")
    print(f"Video Source: {source_name}")
    print(f"Model: {MODEL_PATH} (Inference size: {imgsz}x{imgsz}, Conf: {conf_threshold})")
    print(f"FastAPI Ingestion Endpoint: {BACKEND_ENDPOINT}")
    print(f"Live Web Video Feed: {STREAM_ENDPOINT}")
    print("==================================================")

    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(resolved_source)

    if not cap.isOpened():
        print(f"Error: Unable to open source: {source_name}")
        return

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    poly_points = [
        (int(x * frame_width), int(y * frame_height)) 
        for x, y in ZONE_COORDINATE_RATIOS
    ]
    tripwire_polygon = Polygon(poly_points)
    poly_np = np.array(poly_points, np.int32).reshape((-1, 1, 2))

    zone_map = {
        "cam-01": "ZONE_GATEWAY",
        "cam-02": "ZONE_BRAVO",
        "cam-03": "ZONE_RIVERINE",
        "cam-04": "ZONE_A"
    }
    assigned_zone = zone_map.get(camera_id.lower(), "ZONE_A")

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                # Continuous loop for demo if reading from video file
                if isinstance(resolved_source, str) and os.path.exists(resolved_source):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                if not ret:
                    break

            enhanced_frame, was_enhanced = apply_clahe_enhancement(frame)

            results = model.track(
                source=enhanced_frame,
                classes=list(TARGET_CLASSES.keys()),
                conf=conf_threshold,
                imgsz=imgsz,
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
                        "zone_id": assigned_zone,
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
            cv2.putText(frame, f"CHANNEL: {camera_id.upper()}", (frame_width - 240, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            # Stream annotated frame to web application
            enc_ret, jpeg_buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
            if enc_ret:
                try:
                    frame_stream_queue.put_nowait((camera_id, jpeg_buffer.tobytes()))
                except queue.Full:
                    try:
                        frame_stream_queue.get_nowait()
                        frame_stream_queue.task_done()
                    except queue.Empty:
                        pass
                    try:
                        frame_stream_queue.put_nowait((camera_id, jpeg_buffer.tobytes()))
                    except queue.Full:
                        pass
    except KeyboardInterrupt:
        print("\n[AI Pipeline] Stream stopped by user.")
    finally:
        cap.release()
        payload_queue.put(None)
        frame_stream_queue.put(None)

# ----------------------------------------------------
# 5. ALL-IN-ONE MULTI-CAMERA SURVEILLANCE ENGINE
# ----------------------------------------------------
ALL_CAMERAS_PLAN = [
    {
        "cam_id": "cam-04",
        "name": "CAM-04 · NORTH PERIMETER",
        "source": VIDEO_PRESETS["1"],
        "zone_id": "ZONE_A"
    },
    {
        "cam_id": "cam-02",
        "name": "CAM-02 · FENCE BRAVO",
        "source": VIDEO_PRESETS["2"],
        "zone_id": "ZONE_BRAVO"
    },
    {
        "cam_id": "cam-03",
        "name": "CAM-03 · RIVERINE WATCH",
        "source": VIDEO_PRESETS["3"],
        "zone_id": "ZONE_RIVERINE"
    },
    {
        "cam_id": "cam-01",
        "name": "CAM-01 · GATE ALPHA",
        "source": VIDEO_PRESETS["3"],
        "zone_id": "ZONE_GATEWAY"
    }
]

def camera_stream_worker(cam_cfg, model, stop_event, imgsz=480, conf_threshold=0.35):
    cam_id = cam_cfg["cam_id"]
    source = cam_cfg["source"]
    zone_id = cam_cfg["zone_id"]
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[{cam_id.upper()}] Failed to open source: {source}")
        return

    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    poly_points = [(int(x * frame_w), int(y * frame_h)) for x, y in ZONE_COORDINATE_RATIOS]
    tripwire_poly = Polygon(poly_points)
    poly_np = np.array(poly_points, np.int32).reshape((-1, 1, 2))

    print(f"[{cam_id.upper()}] Running live AI tracking on: {os.path.basename(str(source))}")

    while not stop_event.is_set() and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            if isinstance(source, str) and os.path.exists(source):
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
            if not ret:
                break

        enhanced, was_enhanced = apply_clahe_enhancement(frame)
        results = model.track(
            source=enhanced,
            classes=list(TARGET_CLASSES.keys()),
            conf=conf_threshold,
            imgsz=imgsz,
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
                in_zone = tripwire_poly.contains(bottom_center)

                frame_b64 = None
                if in_zone:
                    crop = frame[max(0, y1):min(frame_h, y2), max(0, x1):min(frame_w, x2)]
                    if crop.size > 0:
                        _, buffer = cv2.imencode('.jpg', crop)
                        frame_b64 = base64.b64encode(buffer).decode('utf-8')

                payload = {
                    "object_class": str(TARGET_CLASSES.get(cls_id, "unknown")),
                    "confidence": float(round(float(conf), 2)),
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "track_id": int(track_id),
                    "in_zone": bool(in_zone),
                    "zone_id": zone_id,
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
        cv2.putText(frame, f"CHANNEL: {cam_id.upper()}", (frame_w - 240, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        enc_ret, jpeg_buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        if enc_ret:
            try:
                frame_stream_queue.put_nowait((cam_id, jpeg_buffer.tobytes()))
            except queue.Full:
                try:
                    frame_stream_queue.get_nowait()
                    frame_stream_queue.task_done()
                except queue.Empty:
                    pass
                try:
                    frame_stream_queue.put_nowait((cam_id, jpeg_buffer.tobytes()))
                except queue.Full:
                    pass

        # Smooth pacing for multi-camera CPU stability
        time.sleep(0.035)

    cap.release()

def run_all_cameras(conf_threshold=0.35, imgsz=480):
    print("==================================================")
    print("  SIMA-DRISHTI FULL MULTI-CAMERA SURVEILLANCE GRID")
    print("==================================================")
    print("Spawning simultaneous AI pipelines across all 4 cameras:")
    for cfg in ALL_CAMERAS_PLAN:
        print(f"  • {cfg['cam_id'].upper()} -> {os.path.basename(str(cfg['source']))} ({cfg['zone_id']})")
    print(f"FastAPI Ingestion Endpoint: {BACKEND_ENDPOINT}")
    print(f"Live Web Video Feed: {STREAM_ENDPOINT}")
    print("==================================================")

    model = YOLO(MODEL_PATH)
    stop_event = threading.Event()
    threads = []

    for cfg in ALL_CAMERAS_PLAN:
        t = threading.Thread(
            target=camera_stream_worker,
            args=(cfg, model, stop_event, imgsz, conf_threshold),
            daemon=True
        )
        threads.append(t)
        t.start()

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[AI Pipeline] Stopping all cameras...")
        stop_event.set()
        for t in threads:
            t.join(timeout=1.0)
        payload_queue.put(None)
        frame_stream_queue.put(None)
        print("[AI Pipeline] All cameras stopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sima-Drishti AI Edge Surveillance Pipeline")
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run simultaneous multi-camera surveillance grid across all cameras (cam-01, cam-02, cam-03, cam-04)"
    )
    parser.add_argument(
        "--source", "-s", "--video", "-v",
        default="1",
        help="Video preset (1/person, 2/dog, 3/fence, 0/webcam) or file path"
    )
    parser.add_argument(
        "--cam", "-c",
        default="cam-04",
        help="Camera channel ID (cam-04, cam-02, cam-01, cam-03)"
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.35,
        help="Detection confidence threshold (default: 0.35)"
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Inference image resolution (default: 640)"
    )
    args = parser.parse_args()

    if args.all:
        run_all_cameras(
            conf_threshold=args.conf,
            imgsz=args.imgsz if args.imgsz != 640 else 480
        )
    else:
        run_pipeline(
            source=args.source,
            camera_id=args.cam,
            conf_threshold=args.conf,
            imgsz=args.imgsz
        )