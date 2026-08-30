from typing import Dict, Tuple
from collections import defaultdict
from app.schemas import DetectionPayload

class FusionEngine:
    """
    Fuses object class, zone boundaries, and frame persistence
    to filter noise and prevent false positives.
    """
    def __init__(self, persistence_threshold: int = 5):
        self.persistence_threshold = persistence_threshold
        self.allowed_classes = {"person", "car", "truck", "bus"}
        # track_id -> consecutive valid frame count
        self.track_history: Dict[int, int] = defaultdict(int)

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

        if current_count >= self.persistence_threshold:
            return True, f"Confirmed alert for {detection.object_class} (persisted {current_count} frames)"

        return False, f"Tracking persistence: {current_count}/{self.persistence_threshold}"

fusion_engine = FusionEngine(persistence_threshold=5)