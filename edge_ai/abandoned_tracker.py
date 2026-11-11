"""
Abandoned Object & Stationary Luggage Tracker
Tracks bags, backpacks, and suitcases. Evaluates stationary duration and owner detachment.
"""

import time
import math
from typing import List, Dict, Any, Tuple


class AbandonedObjectTracker:
    """
    Tracks luggage items (backpack, handbag, suitcase).
    Triggers alert when a bag remains stationary without an owner nearby for > threshold seconds.
    """

    def __init__(self, stationary_threshold_sec: float = 8.0, distance_threshold_px: float = 120.0):
        self.stationary_threshold_sec = stationary_threshold_sec
        self.distance_threshold_px = distance_threshold_px
        
        # Track state: { object_id: { "class_name": str, "center": (x, y), "first_seen": float, "last_seen": float, "alert_sent": bool } }
        self.tracked_objects: Dict[str, Dict[str, Any]] = {}
        self.next_obj_id = 1

    def update(
        self,
        detections: List[Dict[str, Any]],
        current_time: float = None
    ) -> List[Dict[str, Any]]:
        """
        Updates tracking state with new frame detections.
        Returns list of abandoned object alerts.
        """
        if current_time is None:
            current_time = time.time()

        luggage_items = [d for d in detections if d.get("class_name", "").lower() in ["backpack", "handbag", "suitcase"]]
        persons = [d for d in detections if d.get("class_name", "").lower() == "person"]

        alerts = []
        matched_track_ids = set()

        for item in luggage_items:
            cx, cy = item["center"]
            # Match to existing tracked object if close
            matched_id = None
            for track_id, track in self.tracked_objects.items():
                tcx, tcy = track["center"]
                dist = math.hypot(cx - tcx, cy - tcy)
                if dist < 40.0:  # Same location
                    matched_id = track_id
                    break

            if matched_id is not None:
                # Update existing track
                track = self.tracked_objects[matched_id]
                track["last_seen"] = current_time
                track["bbox"] = item["bbox"]
                track["confidence"] = item["confidence"]
                matched_track_ids.add(matched_id)

                # Check stationary duration
                duration = current_time - track["first_seen"]
                
                # Check distance to nearest person
                min_person_dist = float("inf")
                for p in persons:
                    pcx, pcy = p["center"]
                    p_dist = math.hypot(cx - pcx, cy - pcy)
                    if p_dist < min_person_dist:
                        min_person_dist = p_dist

                # If stationary for > threshold and owner detached (> distance_threshold_px or no persons)
                if duration >= self.stationary_threshold_sec and min_person_dist > self.distance_threshold_px:
                    alerts.append({
                        "object_id": matched_id,
                        "class_name": track["class_name"],
                        "detection_type": "Abandoned Object",
                        "object_detected": f"Abandoned {track['class_name']}",
                        "severity": "HIGH",
                        "stationary_duration": round(duration, 1),
                        "bbox": item["bbox"],
                        "confidence": item["confidence"],
                        "nearest_person_dist": round(min_person_dist, 1)
                    })
            else:
                # Register new object track
                new_id = f"OBJ-{self.next_obj_id:03d}"
                self.next_obj_id += 1
                self.tracked_objects[new_id] = {
                    "class_name": item["class_name"],
                    "center": (cx, cy),
                    "bbox": item["bbox"],
                    "confidence": item["confidence"],
                    "first_seen": current_time,
                    "last_seen": current_time,
                    "alert_sent": False
                }
                matched_track_ids.add(new_id)

        # Cleanup lost tracks (older than 10 seconds)
        to_delete = [
            tid for tid, trk in self.tracked_objects.items()
            if (current_time - trk["last_seen"]) > 10.0
        ]
        for tid in to_delete:
            del self.tracked_objects[tid]

        return alerts
