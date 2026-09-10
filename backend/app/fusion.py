import time
import math
from typing import Dict, Tuple, List
from collections import defaultdict
from app.schemas import DetectionPayload

class FusionEngine:
    """
    4-Way Tactical Agreement Fusion Engine:
    Mandates 4 independent criteria agreements before confirming alert:
      1. Class Verification (Threat class person/vehicle, confidence check)
      2. Zone Boundary (Target inside tactical tripwire/geofence vector)
      3. Trajectory Vector (Dynamic track movement / displacement vector)
      4. Dwell Time (Persistence duration inside exclusion zone >= min_dwell)
    """
    def __init__(
        self, 
        persistence_threshold: int = 4, 
        min_dwell_seconds: float = 0.8,
        min_displacement_px: float = 3.0,
        cooldown_seconds: float = 8.0, 
        track_ttl_seconds: float = 60.0
    ):
        self.persistence_threshold = persistence_threshold
        self.min_dwell_seconds = min_dwell_seconds
        self.min_displacement_px = min_displacement_px
        self.cooldown_seconds = cooldown_seconds
        self.track_ttl_seconds = track_ttl_seconds
        
        self.allowed_classes = {"person", "car", "truck", "bus", "motorcycle"}
        
        # composite_track_key (zone_id:track_id) -> consecutive valid frame count in zone
        self.track_history: Dict[str, int] = defaultdict(int)
        # composite_track_key -> timestamp when target first entered zone
        self.track_first_seen_in_zone: Dict[str, float] = {}
        # composite_track_key -> list of recent centroid positions: [(cx, cy, timestamp), ...]
        self.track_positions: Dict[str, List[Tuple[float, float, float]]] = defaultdict(list)
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
            self.track_first_seen_in_zone.pop(tid, None)
            self.track_positions.pop(tid, None)
            self.last_alert_time.pop(tid, None)
            self.track_last_seen.pop(tid, None)
        return len(expired)

    def process(self, detection: DetectionPayload) -> Tuple[bool, str]:
        current_time = time.time()
        track_key = f"{detection.zone_id or 'default'}:{detection.track_id}"
        self.track_last_seen[track_key] = current_time
        self.cleanup_expired_tracks(current_time)

        # ----------------------------------------------------
        # 1. MANDATE 1: CLASS VERIFICATION
        # ----------------------------------------------------
        obj_class = (detection.object_class or "").lower().strip()
        if obj_class not in self.allowed_classes:
            self.track_history.pop(track_key, None)
            self.track_first_seen_in_zone.pop(track_key, None)
            self.track_positions.pop(track_key, None)
            return False, f"[M1 FAIL: CLASS] Non-threat target class: '{obj_class}' (Allowed: {list(self.allowed_classes)})"

        # ----------------------------------------------------
        # 2. MANDATE 2: ZONE BOUNDARY
        # ----------------------------------------------------
        if not detection.in_zone:
            self.track_history[track_key] = 0
            self.track_first_seen_in_zone.pop(track_key, None)
            return False, f"[M2 FAIL: ZONE] Target '{obj_class}' outside tactical boundary vector"

        # Compute centroid from bounding box [x1, y1, x2, y2]
        bbox = detection.bbox or [0, 0, 0, 0]
        cx = (bbox[0] + bbox[2]) / 2.0 if len(bbox) >= 4 else 0.0
        cy = (bbox[1] + bbox[3]) / 2.0 if len(bbox) >= 4 else 0.0

        # Record position history (max last 10 points)
        positions = self.track_positions[track_key]
        positions.append((cx, cy, current_time))
        if len(positions) > 10:
            positions.pop(0)

        # Record first seen time in zone
        if track_key not in self.track_first_seen_in_zone:
            self.track_first_seen_in_zone[track_key] = current_time

        self.track_history[track_key] += 1
        current_frames = self.track_history[track_key]
        dwell_time = current_time - self.track_first_seen_in_zone[track_key]

        # ----------------------------------------------------
        # 3. MANDATE 3: TRAJECTORY VECTOR AGREEMENT
        # ----------------------------------------------------
        if len(positions) >= 2:
            dx = positions[-1][0] - positions[0][0]
            dy = positions[-1][1] - positions[0][1]
            displacement = math.sqrt(dx * dx + dy * dy)
        else:
            displacement = 0.0
            dx, dy = 0.0, 0.0

        # Target must demonstrate active trajectory displacement (moving entity, not static camera noise)
        if current_frames >= 6 and displacement < self.min_displacement_px:
            return False, f"[M3 FAIL: TRAJECTORY] Zero displacement ({displacement:.1f}px). Static background artefact."

        # ----------------------------------------------------
        # 4. MANDATE 4: DWELL TIME AGREEMENT
        # ----------------------------------------------------
        if current_frames < self.persistence_threshold or dwell_time < self.min_dwell_seconds:
            return False, (
                f"[M4 PENDING: DWELL] Frames {current_frames}/{self.persistence_threshold}, "
                f"Dwell {dwell_time:.2f}s/{self.min_dwell_seconds}s (Awaiting 4-way agreement)"
            )

        # ----------------------------------------------------
        # ALL 4 MANDATES AGREED! Check Cooldown
        # ----------------------------------------------------
        last_alert = self.last_alert_time.get(track_key, 0.0)
        if (current_time - last_alert) < self.cooldown_seconds:
            return False, f"[4-WAY AGREED // COOLDOWN] Target {track_key} in debounce ({int(self.cooldown_seconds - (current_time - last_alert))}s remaining)"

        self.last_alert_time[track_key] = current_time
        return True, (
            f"4-WAY AGREEMENT CONFIRMED [CLASS: {obj_class} | ZONE: BOUNDARY_ACTIVE | "
            f"TRAJECTORY: dx={dx:.1f}px, dy={dy:.1f}px (dist={displacement:.1f}px) | "
            f"DWELL: {dwell_time:.2f}s ({current_frames} frames)]"
        )

fusion_engine = FusionEngine(
    persistence_threshold=4, 
    min_dwell_seconds=0.8,
    min_displacement_px=3.0,
    cooldown_seconds=8.0, 
    track_ttl_seconds=60.0
)