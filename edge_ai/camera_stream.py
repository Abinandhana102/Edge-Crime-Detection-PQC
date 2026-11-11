"""
Camera Stream Reader & Synthetic Demonstration Generator
Supports Webcam (0), RTSP/IP Streams, Local Video Files, and Synthetic CCTV Simulation.
"""

import time
import math
from typing import Optional, Tuple
import cv2
import numpy as np


class CameraStream:
    """
    Unified Camera Stream source.
    Handles physical webcams, RTSP streams, pre-recorded video files, and synthetic CCTV footage generator.
    """

    def __init__(
        self,
        source: str = "demo",
        camera_code: str = "CAM-01",
        location: str = "Main Gate North",
        fps: int = 15,
        resolution: Tuple[int, int] = (640, 480)
    ):
        self.source = str(source).strip()
        self.camera_code = camera_code
        self.location = location
        self.fps = fps
        self.width, self.height = resolution
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_opened = False
        
        # Synthetic Demo Simulation State
        self.frame_count = 0
        self.sim_person_x = 50.0
        self.sim_person_y = 260.0
        self.sim_weapon_active = False
        self.sim_bag_abandoned = False

        self._initialize_stream()

    def _initialize_stream(self):
        """Opens capture source or initializes simulation mode"""
        if self.source.lower() == "webcam" or self.source == "0":
            try:
                self.cap = cv2.VideoCapture(0)
                if self.cap.isOpened():
                    self.is_opened = True
                    print(f"[CameraStream] Opened physical webcam for {self.camera_code}")
                    return
            except Exception as e:
                print(f"[CameraStream] Physical webcam unavailable: {e}. Falling back to demo mode.")

        elif self.source.startswith("rtsp://") or self.source.startswith("http://"):
            try:
                self.cap = cv2.VideoCapture(self.source)
                if self.cap.isOpened():
                    self.is_opened = True
                    print(f"[CameraStream] Connected to IP camera stream: {self.source}")
                    return
            except Exception as e:
                print(f"[CameraStream] RTSP source unavailable: {e}. Falling back to demo mode.")

        elif self.source.endswith((".mp4", ".avi", ".mkv", ".mov")):
            try:
                self.cap = cv2.VideoCapture(self.source)
                if self.cap.isOpened():
                    self.is_opened = True
                    print(f"[CameraStream] Opened video file: {self.source}")
                    return
            except Exception as e:
                print(f"[CameraStream] Video file unavailable: {e}. Falling back to demo mode.")

        # Fallback / Default: Synthetic Demo Generator
        self.source = "demo"
        self.is_opened = True
        print(f"[CameraStream] Initialized Synthetic CCTV Demo Generator for {self.camera_code}")

    def read(self) -> Tuple[bool, np.ndarray]:
        """
        Reads next frame from stream.
        Returns: (success, bgr_frame)
        """
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                if frame.shape[1] != self.width or frame.shape[0] != self.height:
                    frame = cv2.resize(frame, (self.width, self.height))
                return True, frame
            else:
                # Video file loop
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if ret:
                    return True, frame

        # Generate Synthetic CCTV Frame
        return True, self._generate_synthetic_frame()

    def _generate_synthetic_frame(self) -> np.ndarray:
        """
        Generates realistic surveillance frame containing realistic corridor/gate background,
        walking person silhouette, and dynamic interactive elements.
        """
        self.frame_count += 1
        t = self.frame_count / float(self.fps)

        # Background: Modern CCTV Corridor / Entrance Hall
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Floor & Wall gradient
        cv2.rectangle(frame, (0, 0), (self.width, 180), (35, 40, 50), -1)  # Wall
        cv2.rectangle(frame, (0, 180), (self.width, self.height), (25, 28, 35), -1)  # Floor
        
        # Perspective floor tiles
        for x in range(0, self.width, 80):
            cv2.line(frame, (x, 180), (int(x * 1.4 - 100), self.height), (45, 50, 60), 1)
        for y in range(180, self.height, 40):
            cv2.line(frame, (0, y), (self.width, y), (40, 45, 55), 1)

        # Secured Doorway
        cv2.rectangle(frame, (220, 40), (420, 180), (20, 24, 30), -1)
        cv2.rectangle(frame, (220, 40), (420, 180), (0, 180, 255), 2)
        cv2.putText(frame, "SECURED FACILITY ENTRANCE", (230, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 200, 255), 1)

        # Restricted Zone boundary markings on floor
        pts = np.array([[180, 220], [460, 220], [520, 420], [120, 420]], np.int32)
        cv2.polylines(frame, [pts], True, (0, 140, 255), 2)
        cv2.putText(frame, "RESTRICTED PERIMETER ZONE", (190, 215), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 140, 255), 1)

        # Person Walking Animation (Cycles across screen)
        cycle_time = t % 16.0
        # Move person from x=60 to x=480
        self.sim_person_x = 60.0 + (cycle_time / 16.0) * 440.0
        bobbing = math.sin(t * 8.0) * 4.0
        px = int(self.sim_person_x)
        py = int(self.sim_person_y + bobbing)

        # Draw Person Silhouette
        # Head
        cv2.circle(frame, (px + 30, py - 60), 18, (180, 190, 200), -1)
        # Torso
        cv2.rectangle(frame, (px + 10, py - 42), (px + 50, py + 40), (50, 70, 120), -1)
        # Legs
        leg_offset = int(math.sin(t * 10.0) * 12.0)
        cv2.line(frame, (px + 20, py + 40), (px + 15 + leg_offset, py + 100), (40, 50, 70), 8)
        cv2.line(frame, (px + 40, py + 40), (px + 45 - leg_offset, py + 100), (40, 50, 70), 8)

        # Trigger Weapon in hand between t=6.0s and t=12.0s in cycle
        if 5.0 <= cycle_time <= 11.0:
            # Draw Hand holding Weapon (Gun/Knife)
            cv2.rectangle(frame, (px + 50, py - 10), (px + 85, py + 2), (20, 20, 20), -1)  # Gun barrel
            cv2.rectangle(frame, (px + 60, py + 2), (px + 72, py + 20), (30, 30, 30), -1)   # Handle
            cv2.putText(frame, "[WEAPON CARRIER]", (px - 10, py - 85), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)

        # Abandoned Bag left at x=300 when cycle_time > 8.0s
        if cycle_time >= 8.0:
            cv2.rectangle(frame, (290, 310), (340, 350), (40, 80, 140), -1)
            cv2.rectangle(frame, (305, 295), (325, 310), (20, 40, 80), 2)  # Handle
            cv2.putText(frame, "[LUGGAGE]", (285, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 200, 0), 1)

        # Realistic CCTV Scanlines & Digital Grain
        noise = np.random.randint(-5, 6, (self.height, self.width, 3), dtype=np.int16)
        frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        # CCTV Timestamp & Camera Watermark (bottom-left)
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"{self.camera_code} - {self.location}", (15, self.height - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.putText(frame, f"REC [●] {now_str}", (15, self.height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        return frame

    def release(self):
        if self.cap is not None:
            self.cap.release()
