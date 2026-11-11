"""
Event Debounce & Incident Priority Management Module
Prevents multiple duplicate alert spam while a threat remains in the camera frame.
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple


class EventManager:
    """
    Manages alert debouncing, cooldown windows, and unique incident ID dispatch.
    """

    def __init__(self, cooldown_seconds: float = 8.0):
        self.cooldown_seconds = cooldown_seconds
        # Cooldown track: { f"{camera_code}_{detection_type}": last_alert_timestamp }
        self.last_alert_times: Dict[str, float] = {}
        self.incident_counter = 1

    def generate_incident_id(self) -> str:
        """Generates a standardized Incident ID e.g., INC-20260827-0001"""
        today_str = datetime.utcnow().strftime("%Y%m%d")
        inc_id = f"INC-{today_str}-{self.incident_counter:04d}"
        self.incident_counter += 1
        return inc_id

    def should_trigger(
        self,
        camera_code: str,
        detection_type: str,
        current_time: Optional[float] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Determines whether a new incident should be created or suppressed under debounce cooldown.
        Returns: (should_create_incident, reason_or_incident_id)
        """
        if current_time is None:
            current_time = time.time()

        key = f"{camera_code.upper()}_{detection_type.upper()}"
        last_time = self.last_alert_times.get(key, 0.0)

        if (current_time - last_time) >= self.cooldown_seconds:
            # Cooldown passed, allowed to generate new incident
            self.last_alert_times[key] = current_time
            new_id = self.generate_incident_id()
            return True, new_id
        else:
            # Debounced: active ongoing incident
            remaining = round(self.cooldown_seconds - (current_time - last_time), 1)
            return False, f"Debounced (cooldown active, {remaining}s remaining)"
