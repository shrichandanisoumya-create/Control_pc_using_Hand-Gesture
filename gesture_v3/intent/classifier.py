# ==============================================================================
# PROJECT J.A.R.V.I.S — AI HAND GESTURE WORKSTATION
# AUTHOR / CREATOR: Soumya Shrichandani
# COPYRIGHT (C) 2026 SOUMYA SHRICHANDANI. ALL RIGHTS RESERVED.
# ==============================================================================

import time
import math
from gesture_v3 import config


class GestureClassifier:
    """
    Intent Engine V3.1
    States: IDLE, MOVE, CLICK_LEFT, CLICK_RIGHT, SCROLL, FIST
    Draw-mode meta flags: is_toggle, is_draw, is_hover, is_eraser, is_fist, is_call_sign
    """

    def __init__(self):
        self.state = "IDLE"
        self.pinch_confidence = 0.0
        self.last_update = time.time()

        self.THUMB_TIP = 4
        self.INDEX_TIP = 8

    def process(self, landmarks):
        if not landmarks:
            self.state = "IDLE"
            self.pinch_confidence = 0.0
            return self.state, {}

        # ------------------------------------------------------------------ #
        # 1. Pinch distances
        # ------------------------------------------------------------------ #
        thumb  = landmarks[4]
        index  = landmarks[8]
        middle = landmarks[12]
        wrist  = landmarks[0]

        dist_click = math.hypot(thumb.x - index.x,  thumb.y - index.y)
        dist_right = math.hypot(thumb.x - middle.x, thumb.y - middle.y)

        # ------------------------------------------------------------------ #
        # 2. Velocity gate
        # ------------------------------------------------------------------ #
        curr_time = time.time()
        dt = curr_time - self.last_update
        self.last_update = curr_time

        velocity = 0.0
        if hasattr(self, 'prev_wrist'):
            velocity = math.hypot(wrist.x - self.prev_wrist.x,
                                  wrist.y - self.prev_wrist.y) / max(dt, 1e-6)
        self.prev_wrist = wrist

        is_stable = velocity < 2.0

        # Confidence accumulation (for CLICK states only)
        if dist_click < config.PINCH_THRESHOLD_NORM and is_stable:
            self.pinch_confidence += config.CONFIDENCE_GROWTH
            self.pinch_type = "LEFT"
        elif dist_right < config.PINCH_THRESHOLD_NORM and is_stable:
            self.pinch_confidence += config.CONFIDENCE_GROWTH
            self.pinch_type = "RIGHT"
        else:
            self.pinch_confidence -= config.CONFIDENCE_DECAY
        self.pinch_confidence = max(0.0, min(1.0, self.pinch_confidence))

        # ------------------------------------------------------------------ #
        # 3. Finger up/down (tip Y < pip Y means finger extended)
        # ------------------------------------------------------------------ #
        fingers_up = [False] * 5

        # Four fingers: index(8), middle(12), ring(16), pinky(20)
        for i, tip_idx in enumerate([8, 12, 16, 20]):
            pip_idx = tip_idx - 2
            fingers_up[i + 1] = landmarks[tip_idx].y < landmarks[pip_idx].y

        # Thumb: use distance from tip(4) to index MCP(5)
        thumb_tip  = landmarks[4]
        index_mcp  = landmarks[5]
        thumb_out  = math.hypot(thumb_tip.x - index_mcp.x,
                                thumb_tip.y - index_mcp.y) > 0.05
        fingers_up[0] = thumb_out

        # ------------------------------------------------------------------ #
        # 4. Key gesture booleans
        # ------------------------------------------------------------------ #

        # FIST — strict: ALL FOUR fingers must be curled down
        # Also require thumb tucked (not "out") for maximum strictness
        is_fist = (not any(fingers_up[1:])) and (not fingers_up[0])

        is_palm  = all(fingers_up)

        # Peace / Scroll: Index + Middle up, Ring + Pinky down
        is_peace = (fingers_up[1] and fingers_up[2]
                    and not fingers_up[3] and not fingers_up[4])

        # Pinch checks
        dist_index  = math.hypot(landmarks[4].x - landmarks[8].x,
                                  landmarks[4].y - landmarks[8].y)
        dist_middle = math.hypot(landmarks[4].x - landmarks[12].x,
                                  landmarks[4].y - landmarks[12].y)
        is_pinch_index  = dist_index  < config.PINCH_THRESHOLD_NORM
        is_pinch_middle = dist_middle < config.PINCH_THRESHOLD_NORM

        # ------------------------------------------------------------------ #
        # 5. State machine
        # ------------------------------------------------------------------ #
        if is_pinch_index:
            self.state = "CLICK_LEFT"
            self.pinch_confidence = 1.0
        elif is_pinch_middle:
            self.state = "CLICK_RIGHT"
        elif is_peace:
            self.state = "SCROLL"
        elif is_fist:
            self.state = "FIST"
        elif is_palm:
            self.state = "MOVE"
        else:
            self.state = "IDLE"

        # ------------------------------------------------------------------ #
        # 6. Draw-mode helper flags
        # ------------------------------------------------------------------ #

        # Rock Sign: Index + Pinky UP, Middle + Ring DOWN (thumb neutral/tucked)
        is_rock = (fingers_up[1] and not fingers_up[2]
                   and not fingers_up[3] and fingers_up[4])

        # Call Sign / Shaka: Thumb + Pinky extended, Index + Middle + Ring curled
        # Thumb must be out AND pinky up AND index/middle/ring DOWN
        is_call_sign = (fingers_up[0] and not fingers_up[1]
                        and not fingers_up[2] and not fingers_up[3]
                        and fingers_up[4])

        # 1-finger draw: index only up, no pinch
        is_draw_gesture = (fingers_up[1]
                           and not fingers_up[2]
                           and not fingers_up[3]
                           and not fingers_up[4]
                           and not is_pinch_index)

        # 2-finger hover: peace sign
        is_hover_gesture = is_peace

        # 3-finger eraser: index + middle + ring, pinky down
        is_eraser_gesture = (fingers_up[1] and fingers_up[2]
                             and fingers_up[3] and not fingers_up[4])

        return self.state, {
            "confidence":   1.0,
            "pinch_dist":   dist_index,
            "fingers_up":   fingers_up,
            "is_toggle":    is_rock,
            "is_draw":      is_draw_gesture,
            "is_hover":     is_hover_gesture,
            "is_eraser":    is_eraser_gesture,
            "is_fist":      is_fist,
            "is_call_sign": is_call_sign,
        }
