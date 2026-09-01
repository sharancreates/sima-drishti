import time
from typing import Dict, Tuple
from collections import defaultdict
from app.schemas import DetectionPayload

class FusionEngine:
    """
    Day 3 Advanced Fusion: Fuses class checks, tripwire zones, 
    temporal persistence, and alert cooldown/debounce.
    """
    def __init__(self, persistence_threshold: int = 5, cooldown_seconds: float = 8.0):
        self.persistence_threshold = persistence_threshold
        self.cooldown_seconds = cooldown_seconds
        self.allowed_classes = {"person", "car", "truck", "bus"}
        
        # track_id -> consecutive valid frame count
        self.track_history: Dict[int, int] = defaultdict(int)
        # track_id -> last alert timestamp (cooldown)
        self.last_alert_time: Dict[int, float] = {}

    def process(self, detection: DetectionPayload) -> Tuple[bool, str]:
        # Filter 1: Check Target Class
        if detection.object_class.lower() not in self.allowed_classes:
            self.track_history.pop(detection.track_id, None)
            return False, f"Ignored non-target class: {detection.object_class}"

        # Filter 2: Check Tripwire / Zone Presence
        if not detection.in_zone:
            self.track_history[detection.track_id] = 0
            return False, "Object detected outside zone"

        # Filter 3: Temporal Persistence Check
        self.track_history[detection.track_id] += 1
        current_count = self.track_history[detection.track_id]

        if current_count < self.persistence_threshold:
            return False, f"Tracking persistence: {current_count}/{self.persistence_threshold}"

        # Filter 4: Alert Cooldown Check (Avoid Spamming DB & Siren)
        current_time = time.time()
        last_time = self.last_alert_time.get(detection.track_id, 0.0)
        
        if (current_time - last_time) < self.cooldown_seconds:
            return False, f"Alert active for track {detection.track_id} (in cooldown for {int(self.cooldown_seconds - (current_time - last_time))}s)"

        # Mark confirmed and record cooldown timestamp
        self.last_alert_time[detection.track_id] = current_time
        return True, f"Confirmed alert for {detection.object_class} (persisted {current_count} frames)"

fusion_engine = FusionEngine(persistence_threshold=5, cooldown_seconds=8.0)