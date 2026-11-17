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
    High-Precision Intent Engine V3.4 (Rotation-Invariant & Anti-Stutter Edition)
    States: IDLE, MOVE, CLICK_LEFT, CLICK_RIGHT, SCROLL, FIST
    Draw-mode meta flags: is_toggle, is_draw, is_hover, is_eraser, is_fist, is_call_sign, is_thumbs_up
    """

    def __init__(self):
        self.state = "IDLE"
        self.pinch_confidence = 0.0
        self.last_update = time.time()
        self.draw_hysteresis = 0  # Stroke continuation buffer to prevent line breaks

        self.THUMB_TIP = 4
        self.INDEX_TIP = 8

    def process(self, landmarks):
        if not landmarks:
            self.state = "IDLE"
            self.pinch_confidence = 0.0
            self.draw_hysteresis = 0
            return self.state, {}

        # ------------------------------------------------------------------ #
        # 1. Landmarks & Pinch distances
        # ------------------------------------------------------------------ #
        wrist  = landmarks[0]
        thumb  = landmarks[4]
        index  = landmarks[8]
        middle = landmarks[12]

        dist_click = math.hypot(thumb.x - index.x,  thumb.y - index.y)
        dist_right = math.hypot(thumb.x - middle.x, thumb.y - middle.y)

        # ------------------------------------------------------------------ #
        # 2. Velocity gate for stable clicks
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
        # 3. Rotation-Invariant Finger Extension Engine
        # Uses both Euclidean distance from wrist and directional vectors
        # Works seamlessly whether hand is vertical, horizontal, or tilted
        # ------------------------------------------------------------------ #
        fingers_up = [False] * 5

        # Four fingers: index(8), middle(12), ring(16), pinky(20)
        for i, tip_idx in enumerate([8, 12, 16, 20]):
            pip_idx = tip_idx - 2
            mcp_idx = tip_idx - 3
            d_tip = math.hypot(landmarks[tip_idx].x - wrist.x, landmarks[tip_idx].y - wrist.y)
            d_pip = math.hypot(landmarks[pip_idx].x - wrist.x, landmarks[pip_idx].y - wrist.y)
            d_mcp = math.hypot(landmarks[tip_idx].x - landmarks[mcp_idx].x, landmarks[tip_idx].y - landmarks[mcp_idx].y)
            
            # Distance-based extension: tip must be further from wrist than PIP AND extended from knuckle
            extended_dist = (d_tip > d_pip * 1.08) and (d_mcp > 0.12)
            # Upright Y-axis check: tip is above PIP AND PIP is above MCP
            extended_y = (landmarks[tip_idx].y < landmarks[pip_idx].y) and (landmarks[pip_idx].y < landmarks[mcp_idx].y)
            fingers_up[i + 1] = extended_dist or extended_y

        # Thumb: check distance from tip to index MCP and from wrist
        thumb_tip  = landmarks[4]
        thumb_ip   = landmarks[3]
        index_mcp  = landmarks[5]
        d_thumb_tip = math.hypot(thumb_tip.x - wrist.x, thumb_tip.y - wrist.y)
        d_thumb_ip  = math.hypot(thumb_ip.x - wrist.x, thumb_ip.y - wrist.y)
        d_thumb_mcp = math.hypot(thumb_tip.x - index_mcp.x, thumb_tip.y - index_mcp.y)
        thumb_out   = (d_thumb_mcp > 0.055) and (d_thumb_tip > d_thumb_ip * 1.04)
        fingers_up[0] = thumb_out

        # ------------------------------------------------------------------ #
        # 4. Key Gestures & Advanced Flags
        # ------------------------------------------------------------------ #

        # Distance of each fingertip to its MCP knuckle
        d_idx_mcp = math.hypot(landmarks[8].x - landmarks[5].x, landmarks[8].y - landmarks[5].y)
        d_mid_mcp = math.hypot(landmarks[12].x - landmarks[9].x, landmarks[12].y - landmarks[9].y)
        d_rng_mcp = math.hypot(landmarks[16].x - landmarks[13].x, landmarks[16].y - landmarks[13].y)
        d_pnk_mcp = math.hypot(landmarks[20].x - landmarks[17].x, landmarks[20].y - landmarks[17].y)
        d_thumb_idx = math.hypot(thumb_tip.x - index_mcp.x, thumb_tip.y - index_mcp.y)

        # Count curled fingers
        curled_fingers = sum(1 for d in (d_idx_mcp, d_mid_mcp, d_rng_mcp, d_pnk_mcp) if d < 0.14)

        # Distinct Thumb States:
        # In a Thumbs-Up: thumb stands tall above wrist and index MCP
        thumb_is_up = (thumb_tip.y < wrist.y - 0.05) and (thumb_tip.y < index_mcp.y - 0.01) and (d_thumb_idx > 0.055)
        # In a Fist: thumb is folded / tucked over fingers (below or level with index MCP)
        thumb_is_tucked = (thumb_tip.y >= index_mcp.y - 0.01) or (d_thumb_idx < 0.065)

        # Call Sign / Shaka (GTA V Color Wheel):
        # Thumb & Pinky extended OUTWARD, center 3 fingers curled into fist
        is_call_sign = (thumb_is_up
                        and d_pnk_mcp > 0.12
                        and d_idx_mcp < 0.14
                        and d_mid_mcp < 0.14
                        and d_rng_mcp < 0.14)

        # Thumbs-Up (Sleep / Wake Toggle):
        # Thumb pointing UP/OUT, 4 fingers (including pinky) curled into fist
        is_thumbs_up = (thumb_is_up
                        and curled_fingers >= 3
                        and d_idx_mcp < 0.14
                        and d_mid_mcp < 0.14
                        and d_pnk_mcp < 0.12
                        and not is_call_sign)

        # Fist (Drag & Drop):
        # All 4 fingers curled into palm AND thumb tucked/folded across fingers (NOT pointing up)
        # 100% mutually exclusive with Thumbs-Up!
        is_fist = (curled_fingers >= 4) and thumb_is_tucked and (not is_thumbs_up)

        # Palm: all fingers extended
        is_palm = all(fingers_up)

        # Peace / Scroll: Index + Middle up, Ring + Pinky down
        is_peace = (fingers_up[1] and fingers_up[2]
                    and not fingers_up[3] and not fingers_up[4])

        # Rock Sign: Index + Pinky UP, Middle + Ring DOWN (Hold 0.8s to toggle Air Canvas)
        is_rock = (fingers_up[1] and not fingers_up[2]
                   and not fingers_up[3] and fingers_up[4])

        # Pinch checks
        dist_index  = math.hypot(thumb.x - index.x, thumb.y - index.y)
        dist_middle = math.hypot(thumb.x - middle.x, thumb.y - middle.y)
        is_pinch_index  = dist_index  < config.PINCH_THRESHOLD_NORM
        is_pinch_middle = dist_middle < config.PINCH_THRESHOLD_NORM

        # ------------------------------------------------------------------ #
        # 5. State machine (Normal Mouse Mode)
        # ------------------------------------------------------------------ #
        if is_pinch_index:
            self.state = "CLICK_LEFT"
            self.pinch_confidence = 1.0
        elif is_pinch_middle:
            self.state = "CLICK_RIGHT"
        elif is_peace:
            self.state = "SCROLL"
        elif is_fist and not is_thumbs_up:
            self.state = "FIST"
        elif is_palm:
            self.state = "MOVE"
        else:
            self.state = "IDLE"

        # ------------------------------------------------------------------ #
        # 6. Advanced Gesture Flags (Air-Canvas & Sleep)
        # ------------------------------------------------------------------ #

        # 3-finger eraser: index + middle + ring, pinky down
        is_eraser_gesture = (fingers_up[1] and fingers_up[2]
                             and fingers_up[3] and not fingers_up[4])

        # 1-finger draw with anti-stutter hysteresis
        # Index extended, middle and ring curled, not pinching, not erasing, not call-sign
        raw_draw = (fingers_up[1]
                    and not fingers_up[2]
                    and not fingers_up[3]
                    and not is_pinch_index
                    and not is_eraser_gesture
                    and not is_call_sign
                    and not is_thumbs_up)

        if raw_draw:
            self.draw_hysteresis = 2
            is_draw_gesture = True
        elif self.draw_hysteresis > 0 and not is_peace and not is_fist and not is_eraser_gesture and not is_call_sign:
            self.draw_hysteresis -= 1
            is_draw_gesture = True
        else:
            self.draw_hysteresis = 0
            is_draw_gesture = False

        # 2-finger hover: peace sign
        is_hover_gesture = is_peace

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
            "is_thumbs_up": is_thumbs_up,
        }
