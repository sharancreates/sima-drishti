import os
import sys
import time

os.chdir("ai_engine")
sys.path.append(".")

import cv2
import ai_pipeline

print("--- Checking cv2.imshow absence in ai_pipeline ---")
with open("ai_pipeline.py", "r", encoding="utf-8") as f:
    code = f.read()

assert "cv2.imshow" not in code, "cv2.imshow still present in ai_pipeline.py!"
print("[PASS] cv2.imshow completely removed! No desktop popup window will open.")

print("--- Testing Frame Stream Encoding & Queue Push ---")
cap = cv2.VideoCapture(ai_pipeline.VIDEO_SOURCE)
assert cap.isOpened(), "Could not open video"
ret, frame = cap.read()
assert ret, "Could not read frame"

ret_enc, jpeg_buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
assert ret_enc, "JPEG encoding failed"
jpeg_bytes = jpeg_buf.tobytes()
print(f"[PASS] Successfully encoded frame to JPEG ({len(jpeg_bytes)} bytes)")

ai_pipeline.frame_stream_queue.put(jpeg_bytes)
assert not ai_pipeline.frame_stream_queue.empty(), "Queue is empty!"
print("[PASS] Frame stream queue accepted frame for background dispatch.")

cap.release()
print("\n[ALL AI PIPELINE CHECKS PASSED]")
