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
BACKEND_ENDPOINT = os.getenv("BACKEND_ENDPOINT", "http://127.0.0.1:8000/detection")
API_KEY = os.getenv("API_KEY", "sima-drishti-secure-key-2026")
STREAM_ENDPOINT = os.getenv("STREAM_ENDPOINT", "http://127.0.0.1:8000/stream/frame")

TARGET_CLASSES = {0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 7: "truck", 16: "dog"}

ZONE_COORDINATE_RATIOS = [
    (0.08, 0.30),
    (0.92, 0.30),
    (0.96, 0.92),
    (0.04, 0.92)
]

# ----------------------------------------------------
# 2. ASYNC BACKGROUND HTTP DISPATCHER & HIGH-THROUGHPUT STREAMER
# ----------------------------------------------------
payload_queue = queue.Queue(maxsize=128)

# Latest frame store per camera channel (non-blocking, zero queue lockups)
latest_camera_frames = {}
latest_camera_frames_lock = threading.Lock()

def update_stream_frame(cam_id: str, frame_bytes: bytes):
    """Safely updates latest encoded frame for a given camera channel."""
    with latest_camera_frames_lock:
        latest_camera_frames[cam_id.lower()] = (frame_bytes, time.time())

def backend_sender_worker():
    """Consumes detection payloads from queue and dispatches to FastAPI fusion engine."""
    session = requests.Session()
    api_key_header = {"X-API-Key": API_KEY}
    session.headers.update(api_key_header)
    while True:
        try:
            payload = payload_queue.get(timeout=0.5)
        except queue.Empty:
            continue
        if payload is None:
            break
        try:
            response = session.post(BACKEND_ENDPOINT, json=payload, headers=api_key_header, timeout=0.8)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ALERT_CONFIRMED":
                    print(f"🚨 [ALERT CONFIRMED BY FUSION ENGINE] Alert ID: {data.get('alert_id')} | Zone: {payload.get('zone_id')}")
        except requests.exceptions.RequestException:
            pass
        finally:
            payload_queue.task_done()

def camera_stream_sender(cam_id: str, stop_event: threading.Event):
    """Dedicated lightweight streaming worker per active camera (runs at ~22 FPS)."""
    session = requests.Session()
    target_cam = cam_id.lower()
    headers = {
        "Content-Type": "image/jpeg",
        "X-Camera-ID": target_cam
    }
    url = f"{STREAM_ENDPOINT}?cam_id={target_cam}"
    last_sent_timestamp = 0.0

    while not stop_event.is_set():
        frame_bytes = None
        ts = 0.0
        with latest_camera_frames_lock:
            if target_cam in latest_camera_frames:
                frame_bytes, ts = latest_camera_frames[target_cam]

        if frame_bytes and ts > last_sent_timestamp:
            last_sent_timestamp = ts
            try:
                session.post(url, data=frame_bytes, headers=headers, timeout=0.3)
            except Exception:
                pass
        time.sleep(0.045)  # ~22 FPS pacing to backend

network_thread = threading.Thread(target=backend_sender_worker, daemon=True)
network_thread.start()

# ----------------------------------------------------
# 3. HIGH-SPEED LOW-LIGHT MODULE (< 1ms execution)
# ----------------------------------------------------
def apply_clahe_enhancement(frame, brightness_threshold=115):
    """Ultra-fast L-channel CLAHE enhancement with adaptive contrast boost for dusk/low-light videos."""
    small = cv2.resize(frame, (64, 36), interpolation=cv2.INTER_NEAREST)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    if np.mean(gray) < brightness_threshold:
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)
        merged = cv2.merge((l_enhanced, a, b))
        return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR), True
    return frame, False

# ----------------------------------------------------
# 4. SINGLE-CAMERA PIPELINE
# ----------------------------------------------------
def run_pipeline(source="1", camera_id="cam-04", conf_threshold=0.25, imgsz=640):
    camera_id = camera_id.lower()
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
    assigned_zone = zone_map.get(camera_id, "ZONE_A")

    stop_event = threading.Event()
    sender_thread = threading.Thread(target=camera_stream_sender, args=(camera_id, stop_event), daemon=True)
    sender_thread.start()

    frame_idx = 0
    active_detections = []
    INFERENCE_INTERVAL = 2

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                if isinstance(resolved_source, str) and os.path.exists(resolved_source):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                if not ret:
                    break

            frame_idx += 1
            run_yolo = (frame_idx % INFERENCE_INTERVAL == 0)

            enhanced_frame, was_enhanced = apply_clahe_enhancement(frame)

            if run_yolo:
                results = model.track(
                    source=enhanced_frame,
                    classes=list(TARGET_CLASSES.keys()),
                    conf=conf_threshold,
                    imgsz=imgsz,
                    persist=True,
                    tracker="bytetrack.yaml",
                    verbose=False
                )

                active_detections = []
                if results[0].boxes is not None and len(results[0].boxes) > 0:
                    boxes = results[0].boxes.xyxy.cpu().numpy()
                    confidences = results[0].boxes.conf.cpu().numpy()
                    class_ids = results[0].boxes.cls.cpu().numpy().astype(int)
                    if results[0].boxes.id is not None:
                        track_ids = results[0].boxes.id.cpu().numpy().astype(int)
                    else:
                        track_ids = [int(i + 1) for i in range(len(boxes))]

                    for bbox, conf, cls_id, track_id in zip(boxes, confidences, class_ids, track_ids):
                        x1, y1, x2, y2 = map(int, bbox)
                        bottom_center = Point(int((x1 + x2) / 2), y2)
                        in_zone = tripwire_polygon.contains(bottom_center)

                        frame_b64 = None
                        if in_zone:
                            crop = frame[max(0, y1):min(frame_height, y2), max(0, x1):min(frame_width, x2)]
                            if crop.size > 0:
                                _, buffer = cv2.imencode('.jpg', crop)
                                frame_b64 = base64.b64encode(buffer).decode('utf-8')

                        raw_class = TARGET_CLASSES.get(cls_id, "unknown")
                        obj_label = "person" if raw_class in ("person", "bicycle", "motorcycle") else raw_class

                        payload = {
                            "object_class": obj_label,
                            "confidence": float(round(float(conf), 2)),
                            "bbox": [int(x1), int(y1), int(x2), int(y2)],
                            "track_id": int(track_id),
                            "in_zone": bool(in_zone),
                            "zone_id": assigned_zone,
                            "camera_id": camera_id,
                            "frame_image": frame_b64,
                            "timestamp": int(time.time())
                        }
                        try:
                            payload_queue.put_nowait(payload)
                        except queue.Full:
                            pass

                        active_detections.append((bbox, conf, cls_id, track_id, in_zone, obj_label))

            # Render zone polygon and active bounding boxes
            cv2.polylines(frame, [poly_np], isClosed=True, color=(0, 0, 255), thickness=2)
            for bbox, conf, cls_id, track_id, in_zone, obj_class in active_detections:
                x1, y1, x2, y2 = map(int, bbox)
                box_color = (0, 0, 255) if in_zone else (0, 255, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                cv2.putText(frame, f"ID:{track_id} {obj_class} {'[BREACH]' if in_zone else ''}",
                            (x1, max(18, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)

            status_text = "CLAHE: ACTIVE" if was_enhanced else "CLAHE: OFF"
            cv2.putText(frame, status_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(frame, f"CHANNEL: {camera_id.upper()}", (frame_width - 240, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            # Resize if large for fast transmission and smooth playback
            if frame_width > 960:
                stream_frame = cv2.resize(frame, (960, int(frame_height * 960 / frame_width)))
            else:
                stream_frame = frame

            enc_ret, jpeg_buffer = cv2.imencode('.jpg', stream_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            if enc_ret:
                update_stream_frame(camera_id, jpeg_buffer.tobytes())

            time.sleep(0.025)

    except KeyboardInterrupt:
        print("\n[AI Pipeline] Stream stopped by user.")
    finally:
        stop_event.set()
        cap.release()
        payload_queue.put(None)

# ----------------------------------------------------
# 5. ALL-IN-ONE MULTI-CAMERA SURVEILLANCE ENGINE
# ----------------------------------------------------
ALL_CAMERAS_PLAN = [
    {
        "cam_id": "cam-04",
        "name": "CAM-04 · NORTH PERIMETER",
        "source": VIDEO_PRESETS["1"],
        "zone_id": "ZONE_A",
        "zone_ratios": [(0.15, 0.40), (0.85, 0.40), (0.95, 0.90), (0.05, 0.90)],
        "start_offset": 0
    },
    {
        "cam_id": "cam-02",
        "name": "CAM-02 · FENCE BRAVO",
        "source": VIDEO_PRESETS["2"],
        "zone_id": "ZONE_BRAVO",
        "zone_ratios": [(0.10, 0.48), (0.90, 0.48), (0.95, 0.92), (0.05, 0.92)],
        "start_offset": 0
    },
    {
        "cam_id": "cam-03",
        "name": "CAM-03 · RIVERINE WATCH",
        "source": VIDEO_PRESETS["3"],
        "zone_id": "ZONE_RIVERINE",
        "zone_ratios": [(0.05, 0.20), (0.95, 0.20), (0.98, 0.95), (0.02, 0.95)],
        "start_offset": 0
    },
    {
        "cam_id": "cam-01",
        "name": "CAM-01 · GATE ALPHA",
        "source": VIDEO_PRESETS["1"],
        "zone_id": "ZONE_GATEWAY",
        "zone_ratios": [(0.12, 0.38), (0.88, 0.38), (0.95, 0.92), (0.05, 0.92)],
        "start_offset": 0
    }
]

def camera_stream_worker(cam_cfg, stop_event, imgsz=640, conf_threshold=0.25):
    """
    Dedicated worker per camera:
    - Runs independent YOLOv8 model instance with isolated ByteTrack state
    - Paces inference every 2nd frame for responsive tracking and smooth video
    - Pushes compressed stream frames to latest_camera_frames
    """
    cam_id = cam_cfg["cam_id"].lower()
    source = cam_cfg["source"]
    zone_id = cam_cfg["zone_id"]
    zone_ratios = cam_cfg.get("zone_ratios", ZONE_COORDINATE_RATIOS)
    start_offset = cam_cfg.get("start_offset", 0)

    # Independent YOLO instance per camera thread: prevents tracker/predictor state cross-talk!
    cam_model = YOLO(MODEL_PATH)

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[{cam_id.upper()}] Failed to open source: {source}")
        return

    if start_offset > 0:
        total_f = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_f > start_offset:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_offset)

    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    poly_points = [(int(x * frame_w), int(y * frame_h)) for x, y in zone_ratios]
    tripwire_poly = Polygon(poly_points)
    poly_np = np.array(poly_points, np.int32).reshape((-1, 1, 2))

    print(f"[{cam_id.upper()}] Running isolated AI tracking on: {os.path.basename(str(source))} (Zone: {zone_id})")

    frame_idx = 0
    active_detections = []
    INFERENCE_INTERVAL = 2  # Paced for high accuracy and smooth ~25 FPS

    while not stop_event.is_set() and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            if isinstance(source, str) and os.path.exists(source):
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
            if not ret:
                break

        frame_idx += 1
        run_yolo = (frame_idx % INFERENCE_INTERVAL == 0)

        enhanced, was_enhanced = apply_clahe_enhancement(frame)

        if run_yolo:
            results = cam_model.track(
                source=enhanced,
                classes=list(TARGET_CLASSES.keys()),
                conf=conf_threshold,
                imgsz=imgsz,
                persist=True,
                tracker="bytetrack.yaml",
                verbose=False
            )

            active_detections = []
            if results[0].boxes is not None and len(results[0].boxes) > 0:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                confidences = results[0].boxes.conf.cpu().numpy()
                class_ids = results[0].boxes.cls.cpu().numpy().astype(int)
                if results[0].boxes.id is not None:
                    track_ids = results[0].boxes.id.cpu().numpy().astype(int)
                else:
                    track_ids = [int(i + 1) for i in range(len(boxes))]

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

                    raw_class = TARGET_CLASSES.get(cls_id, "unknown")
                    obj_label = "person" if raw_class in ("person", "bicycle", "motorcycle") else raw_class

                    payload = {
                        "object_class": obj_label,
                        "confidence": float(round(float(conf), 2)),
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "track_id": int(track_id),
                        "in_zone": bool(in_zone),
                        "zone_id": zone_id,
                        "camera_id": cam_id,
                        "frame_image": frame_b64,
                        "timestamp": int(time.time())
                    }
                    try:
                        payload_queue.put_nowait(payload)
                    except queue.Full:
                        pass

                    active_detections.append((bbox, conf, cls_id, track_id, in_zone, obj_label))

        # Render bounding boxes and zone vector
        cv2.polylines(frame, [poly_np], isClosed=True, color=(0, 0, 255), thickness=2)
        for bbox, conf, cls_id, track_id, in_zone, obj_class in active_detections:
            x1, y1, x2, y2 = map(int, bbox)
            box_color = (0, 0, 255) if in_zone else (0, 255, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
            cv2.putText(frame, f"ID:{track_id} {obj_class} {'[BREACH]' if in_zone else ''}",
                        (x1, max(18, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)

        status_text = "CLAHE: ACTIVE" if was_enhanced else "CLAHE: OFF"
        cv2.putText(frame, status_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(frame, f"CHANNEL: {cam_id.upper()}", (frame_w - 240, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Scale down for fast JPEG encoding & smooth streaming over localhost HTTP
        if frame_w > 800:
            stream_frame = cv2.resize(frame, (800, int(frame_h * 800 / frame_w)))
        else:
            stream_frame = frame

        enc_ret, jpeg_buffer = cv2.imencode('.jpg', stream_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
        if enc_ret:
            update_stream_frame(cam_id, jpeg_buffer.tobytes())

        # Pacing for ~25 FPS smooth video playback
        time.sleep(0.030)

    cap.release()

def run_all_cameras(conf_threshold=0.25, imgsz=640):
    print("==================================================")
    print("  SIMA-DRISHTI FULL MULTI-CAMERA SURVEILLANCE GRID")
    print("==================================================")
    print("Spawning simultaneous isolated AI pipelines across all 4 cameras:")
    for cfg in ALL_CAMERAS_PLAN:
        print(f"  • {cfg['cam_id'].upper()} -> {os.path.basename(str(cfg['source']))} ({cfg['zone_id']})")
    print(f"FastAPI Ingestion Endpoint: {BACKEND_ENDPOINT}")
    print(f"Live Web Video Feed: {STREAM_ENDPOINT}")
    print("==================================================")

    stop_event = threading.Event()
    worker_threads = []
    sender_threads = []

    # Start dedicated stream sender thread per camera (non-blocking, smooth ~22 FPS)
    for cfg in ALL_CAMERAS_PLAN:
        cam_id = cfg["cam_id"].lower()
        st = threading.Thread(
            target=camera_stream_sender,
            args=(cam_id, stop_event),
            daemon=True
        )
        sender_threads.append(st)
        st.start()

    # Start independent camera tracking worker per camera
    for cfg in ALL_CAMERAS_PLAN:
        wt = threading.Thread(
            target=camera_stream_worker,
            args=(cfg, stop_event, imgsz, conf_threshold),
            daemon=True
        )
        worker_threads.append(wt)
        wt.start()

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[AI Pipeline] Stopping all cameras...")
        stop_event.set()
        for t in worker_threads:
            t.join(timeout=1.0)
        for t in sender_threads:
            t.join(timeout=1.0)
        payload_queue.put(None)
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
        default=0.25,
        help="Detection confidence threshold (default: 0.25)"
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
            imgsz=args.imgsz
        )
    else:
        run_pipeline(
            source=args.source,
            camera_id=args.cam,
            conf_threshold=args.conf,
            imgsz=args.imgsz
        )