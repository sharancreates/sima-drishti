import os
import sys
import time
import json
import base64
import requests
import asyncio
import websockets
import cv2
import numpy as np
from shapely.geometry import Point, Polygon
from ultralytics import YOLO

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:5173"
WS_URL = "ws://127.0.0.1:8000/ws/alerts"
API_KEY = "sima-drishti-secure-key-2026"

VIDEO_PATH = os.path.abspath(r"ai_engine\media\WhatsApp Video 2026-08-29 at 11.14.59 PM.mp4")
MODEL_PATH = os.path.abspath(r"ai_engine\yolov8n.pt")

ZONE_COORDINATE_RATIOS = [
    (0.15, 0.40),
    (0.85, 0.40),
    (0.95, 0.90),
    (0.05, 0.90)
]

TARGET_CLASSES = {0: "person", 2: "car", 7: "truck", 16: "dog"}

async def run_e2e_audit():
    print("==================================================")
    print("   SIMA-DRISHTI FULL END-TO-END DEMO-DAY AUDIT   ")
    print("==================================================")

    # 1. Check services
    print("\n--- Step 1: Health & Service Connectivity ---")
    try:
        h_res = requests.get(f"{BACKEND_URL}/health", timeout=3)
        print(f"Backend GET /health: {h_res.status_code} -> {h_res.json()}")
        assert h_res.status_code == 200
    except Exception as e:
        print(f"Backend Health Check FAILED: {e}")
        return

    try:
        f_res = requests.get(FRONTEND_URL, timeout=3)
        print(f"Frontend GET /: {f_res.status_code} (Served by Vite dev server)")
        assert f_res.status_code == 200
    except Exception as e:
        print(f"Frontend HTTP Check FAILED: {e}")
        return

    # 2. Connect WebSocket listener
    print("\n--- Step 2: Connecting WebSocket Client ---")
    ws_received_alerts = []

    async with websockets.connect(WS_URL) as ws:
        print(f"Connected to {WS_URL} successfully!")

        async def listen_ws():
            try:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=6.0)
                    data = json.loads(msg)
                    ws_received_alerts.append(data)
                    print(f"  [WS EVENT RECEIVED]: Alert #{data.get('alert_id')} | {data.get('object_class')} | Zone: {data.get('zone')} | Lat: {data.get('lat')}, Lng: {data.get('lng')}")
            except asyncio.TimeoutError:
                pass

        listener_task = asyncio.create_task(listen_ws())

        # 3. Test Non-threat class filtering (Dog)
        print("\n--- Step 3: Testing Non-Threat Class Rejection (Dog) ---")
        dog_payload = {
            "object_class": "dog",
            "confidence": 0.91,
            "bbox": [100, 200, 300, 400],
            "track_id": 999,
            "in_zone": True,
            "zone_id": "ZONE_A",
            "frame_image": None,
            "timestamp": int(time.time())
        }
        dog_res = requests.post(
            f"{BACKEND_URL}/detection",
            json=dog_payload,
            headers={"X-API-Key": API_KEY},
            timeout=2.0
        )
        print(f"Dog detection response: {dog_res.status_code} -> {dog_res.json()}")
        assert dog_res.json().get("status") == "FILTERED", "Dog was not filtered!"
        print("[PASS] Non-threat class rejected by Fusion Engine.")

        # 4. Stream bundled video through real YOLOv8n + ByteTrack pipeline
        print("\n--- Step 4: Running Bundled Video through Live Pipeline ---")
        model = YOLO(MODEL_PATH)
        cap = cv2.VideoCapture(VIDEO_PATH)
        assert cap.isOpened(), "Failed to open video file"

        frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        poly_points = [(int(x * frame_w), int(y * frame_h)) for x, y in ZONE_COORDINATE_RATIOS]
        tripwire_poly = Polygon(poly_points)

        print(f"Video opened: {frame_w}x{frame_h}. Feeding frames through detector & fusion...")
        
        session = requests.Session()
        session.headers.update({"X-API-Key": API_KEY})

        start_time = time.time()
        first_breach_detection_time = None
        alert_confirmation_time = None
        confirmed_alert_info = None

        frame_idx = 0
        while cap.isOpened() and frame_idx < 80:
            ret, frame = cap.read()
            if not ret:
                break
            frame_idx += 1

            # Run tracking
            results = model.track(
                source=frame,
                classes=list(TARGET_CLASSES.keys()),
                conf=0.35,
                imgsz=960,
                persist=True,
                tracker="bytetrack.yaml",
                verbose=False
            )

            if results[0].boxes and results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                confs = results[0].boxes.conf.cpu().numpy()
                cls_ids = results[0].boxes.cls.cpu().numpy().astype(int)
                tids = results[0].boxes.id.cpu().numpy().astype(int)

                for bbox, conf, cid, tid in zip(boxes, confs, cls_ids, tids):
                    x1, y1, x2, y2 = map(int, bbox)
                    bottom_center = Point(int((x1 + x2) / 2), y2)
                    in_zone = tripwire_poly.contains(bottom_center)

                    if in_zone and first_breach_detection_time is None:
                        first_breach_detection_time = time.time()

                    # Crop thumbnail
                    frame_b64 = None
                    if in_zone:
                        crop = frame[max(0, y1):min(frame_h, y2), max(0, x1):min(frame_w, x2)]
                        if crop.size > 0:
                            _, buf = cv2.imencode('.jpg', crop)
                            frame_b64 = base64.b64encode(buf).decode('utf-8')

                    det_payload = {
                        "object_class": TARGET_CLASSES.get(cid, "person"),
                        "confidence": float(round(float(conf), 2)),
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "track_id": int(tid),
                        "in_zone": bool(in_zone),
                        "zone_id": "ZONE_A",
                        "frame_image": frame_b64,
                        "timestamp": int(time.time())
                    }

                    r = session.post(f"{BACKEND_URL}/detection", json=det_payload, timeout=2.0)
                    resp_json = r.json()

                    if resp_json.get("status") == "ALERT_CONFIRMED":
                        alert_confirmation_time = time.time()
                        confirmed_alert_info = resp_json
                        print(f"  >>> Frame {frame_idx}: ALERT_CONFIRMED! Alert ID: {resp_json.get('alert_id')}")
                        break

            if confirmed_alert_info:
                # Send 5 more frames with same track to test cooldown debounce
                print("\n--- Step 5: Testing Cooldown Debounce with Subsequent Frames ---")
                for c_idx in range(5):
                    det_payload["timestamp"] = int(time.time())
                    c_resp = session.post(f"{BACKEND_URL}/detection", json=det_payload, timeout=2.0).json()
                    print(f"  Subsequent frame +{c_idx+1} under cooldown: status={c_resp.get('status')}, reason={c_resp.get('reason')}")
                    assert c_resp.get("status") == "FILTERED", "Cooldown failed to debounce repeat detections!"
                print("[PASS] Cooldown correctly debounced repeat detections.")
                break

        cap.release()

        # Wait for WS listener
        await listener_task

        print("\n--- Step 6: Verification of Real-Time Alert Delivery & Latency ---")
        if first_breach_detection_time and alert_confirmation_time:
            latency = alert_confirmation_time - first_breach_detection_time
            print(f"Elapsed time from first breach detection to confirmed alert: {latency:.3f} seconds (across 5 persistence frames)")
            print(f"[NOTE] CPU inference wall-clock latency: {latency:.3f}s (due to imgsz=960 inference on CPU).")
            assert latency < 25.0, f"Latency {latency}s was higher than expected"

        print(f"WebSocket alerts captured: {len(ws_received_alerts)}")
        assert len(ws_received_alerts) >= 1, "No alert was broadcast over WebSocket!"
        latest_ws_alert = ws_received_alerts[-1]
        print("WebSocket payload sample:")
        print(json.dumps(latest_ws_alert, indent=2))

        # Check fields
        for field in ["alert_id", "object_class", "zone", "thumbnail", "lat", "lng", "timestamp"]:
            assert field in latest_ws_alert, f"Missing required field in WS payload: {field}"
        print("[PASS] WebSocket alert schema strictly validated.")

        # 7. Check database persistence
        print("\n--- Step 7: Verifying Database Persistence ---")
        db_res = requests.get(f"{BACKEND_URL}/alerts", timeout=2.0)
        alerts_in_db = db_res.json()
        print(f"Total alerts in DB: {len(alerts_in_db)}")
        assert any((a.get("alert_id") == confirmed_alert_info["alert_id"] or a.get("id") == confirmed_alert_info["alert_id"]) for a in alerts_in_db), "Confirmed alert not found in DB!"
        print(f"[PASS] Alert #{confirmed_alert_info['alert_id']} confirmed persisted in SQLite.")

        # 8. Test Tactical Dispatch API
        print("\n--- Step 8: Testing QRT Dispatch Action ---")
        dsp_payload = {
            "alert_id": confirmed_alert_info["alert_id"],
            "unit_id": "alpha",
            "target_sector": "ZONE_A",
            "notes": "E2E automated verification dispatch"
        }
        dsp_res = session.post(f"{BACKEND_URL}/dispatch", json=dsp_payload, timeout=2.0)
        print(f"Dispatch response: {dsp_res.status_code} -> {dsp_res.json()}")
        assert dsp_res.status_code == 200
        print("[PASS] Tactical QRT unit dispatched successfully.")

    print("\n==================================================")
    print("      ALL END-TO-END AUDIT CHECKS PASSED!         ")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_e2e_audit())
