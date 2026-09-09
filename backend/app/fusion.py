import time
from typing import Dict, Tuple
from collections import defaultdict
from app.schemas import DetectionPayload

class FusionEngine:
    """
    Day 3 Advanced Fusion: Fuses class checks, tripwire zones, 
    temporal persistence, and alert cooldown/debounce.
    Includes TTL-based garbage collection to prevent unbounded memory growth.
    """
    def __init__(self, persistence_threshold: int = 5, cooldown_seconds: float = 8.0, track_ttl_seconds: float = 60.0):
        self.persistence_threshold = persistence_threshold
        self.cooldown_seconds = cooldown_seconds
        self.track_ttl_seconds = track_ttl_seconds
        self.allowed_classes = {"person", "car", "truck", "bus"}
        
        # composite_track_key (zone_id:track_id) -> consecutive valid frame count
        self.track_history: Dict[str, int] = defaultdict(int)
        # composite_track_key -> last alert timestamp (cooldown)
        self.last_alert_time: Dict[str, float] = {}
        # composite_track_key -> last seen timestamp for expiration cleanup
        self.track_last_seen: Dict[str, float] = {}

    def cleanup_expired_tracks(self, current_time: float) -> int:
        """Prunes stale tracking data older than track_ttl_seconds to prevent memory leaks."""
        expired = [
            tid for tid, last_seen in self.track_last_seen.items()
            if (current_time - last_seen) > self.track_ttl_seconds
        ]
        for tid in expired:
            self.track_history.pop(tid, None)
            self.last_alert_time.pop(tid, None)
            self.track_last_seen.pop(tid, None)
        return len(expired)

    def process(self, detection: DetectionPayload) -> Tuple[bool, str]:
        current_time = time.time()
        track_key = f"{detection.zone_id or 'default'}:{detection.track_id}"
        self.track_last_seen[track_key] = current_time
        self.cleanup_expired_tracks(current_time)

        # Filter 1: Check Target Class
        if detection.object_class.lower() not in self.allowed_classes:
            self.track_history.pop(track_key, None)
            return False, f"Ignored non-target class: {detection.object_class}"

        # Filter 2: Check Tripwire / Zone Presence
        if not detection.in_zone:
            self.track_history[track_key] = 0
            return False, "Object detected outside zone"

        # Filter 3: Temporal Persistence Check
        self.track_history[track_key] += 1
        current_count = self.track_history[track_key]

        if current_count < self.persistence_threshold:
            return False, f"Tracking persistence: {current_count}/{self.persistence_threshold}"

        # Filter 4: Alert Cooldown Check (Avoid Spamming DB & Siren)
        last_time = self.last_alert_time.get(track_key, 0.0)
        
        if (current_time - last_time) < self.cooldown_seconds:
            return False, f"Alert active for track {track_key} (in cooldown for {int(self.cooldown_seconds - (current_time - last_time))}s)"

        # Mark confirmed and record cooldown timestamp
        self.last_alert_time[track_key] = current_time
        return True, f"Confirmed alert for {detection.object_class} (persisted {current_count} frames)"

fusion_engine = FusionEngine(persistence_threshold=5, cooldown_seconds=8.0, track_ttl_seconds=60.0)