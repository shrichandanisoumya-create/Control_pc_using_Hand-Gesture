# ==============================================================================
# PROJECT J.A.R.V.I.S — AI HAND GESTURE WORKSTATION
# AUTHOR / CREATOR: Soumya Shrichandani
# COPYRIGHT (C) 2026 SOUMYA SHRICHANDANI. ALL RIGHTS RESERVED.
# ==============================================================================

import math
import numpy as np
from gesture_v3 import config

class AdaptiveSmoother:
    """
    Pro-Level Velocity-Adaptive Smoother with Micro-Deadzone.
    Provides rock-solid stability during precision pointing / handwriting
    and ultra-low latency responsiveness during fast movements.
    """
    def __init__(self, deadzone=config.MICRO_DEADZONE_PIXELS, 
                 base_alpha=config.SMOOTHER_BASE_ALPHA, 
                 fast_alpha=config.SMOOTHER_FAST_ALPHA):
        self.deadzone = deadzone
        self.base_alpha = base_alpha
        self.fast_alpha = fast_alpha
        self.prev_x = None
        self.prev_y = None

    def reset(self):
        """Reset filter history (e.g. on hand loss or new stroke)."""
        self.prev_x = None
        self.prev_y = None

    def update(self, target_x, target_y):
        """
        Filter incoming screen coordinates.
        :param target_x: Raw target x coordinate
        :param target_y: Raw target y coordinate
        :return: (smoothed_x, smoothed_y) as integers
        """
        if self.prev_x is None or self.prev_y is None:
            self.prev_x = float(target_x)
            self.prev_y = float(target_y)
            return int(target_x), int(target_y)

        # 1. Micro-deadzone check (anti-tremor / rock-solid stillness)
        dx = target_x - self.prev_x
        dy = target_y - self.prev_y
        dist = math.hypot(dx, dy)

        if dist <= self.deadzone:
            return int(self.prev_x), int(self.prev_y)

        # 2. Dynamic Velocity-Adaptive EMA
        # Ramp from base_alpha (slow, strong smoothing) to fast_alpha (fast, high responsiveness)
        speed_factor = min(1.0, max(0.0, (dist - self.deadzone) / 45.0))
        alpha = self.base_alpha + speed_factor * (self.fast_alpha - self.base_alpha)

        smooth_x = alpha * target_x + (1.0 - alpha) * self.prev_x
        smooth_y = alpha * target_y + (1.0 - alpha) * self.prev_y

        self.prev_x = smooth_x
        self.prev_y = smooth_y

        return int(round(smooth_x)), int(round(smooth_y))
