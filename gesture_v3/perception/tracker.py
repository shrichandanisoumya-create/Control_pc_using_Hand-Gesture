# ==============================================================================
# PROJECT J.A.R.V.I.S — AI HAND GESTURE WORKSTATION
# AUTHOR / CREATOR: Soumya Shrichandani
# COPYRIGHT (C) 2026 SOUMYA SHRICHANDANI. ALL RIGHTS RESERVED.
# ==============================================================================

import mediapipe as mp
import numpy as np
import time
import os
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Relative import fix if needed, but config is in parent
try:
    from .. import config
except ImportError:
    import config

class HandTracker:
    """
    High-Performance MediaPipe Hand Landmarker.
    Uses VIDEO mode with strict monotonic timestamping and optimized single-hand
    tracking to guarantee 60 FPS inference with zero flickering.
    """
    def __init__(self, model_path="hand_landmarker.task"):
        self.model_path = model_path
        if not os.path.exists(self.model_path):
            # Try looking one level up if not found (development convenience)
            if os.path.exists("../" + model_path):
                self.model_path = "../" + model_path
            else:
                raise FileNotFoundError(f"Model not found at {model_path}")

        base_options = python.BaseOptions(model_asset_path=self.model_path)
        
        # High-performance single-hand tracking for maximum speed
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,  # 1 hand gives 2x faster inference and eliminates latency
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self.last_timestamp_ms = -1

    def process(self, image_rgb, timestamp_ms):
        """
        Process a frame with monotonic timestamp guard.
        :param image_rgb: OpenCV Image (RGB)
        :param timestamp_ms: Current timestamp in milliseconds
        :return: Detection result
        """
        # Strictly guarantee monotonically increasing timestamp to prevent MediaPipe drops/crashes
        ts = int(timestamp_ms)
        if ts <= self.last_timestamp_ms:
            ts = self.last_timestamp_ms + 1
        self.last_timestamp_ms = ts

        # Create MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        # Detect
        return self.landmarker.detect_for_video(mp_image, ts)
