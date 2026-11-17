# ==============================================================================
# PROJECT J.A.R.V.I.S — AI HAND GESTURE WORKSTATION
# AUTHOR / CREATOR: Soumya Shrichandani
# COPYRIGHT (C) 2026 SOUMYA SHRICHANDANI. ALL RIGHTS RESERVED.
# ==============================================================================

import cv2
import numpy as np
from collections import deque
from gesture_v3 import config

class CinematicHUD:
    """
    UI Layer.
    Renders "Iron Man" style overlay with anti-flicker trail buffering.
    """
    def __init__(self):
        # Trail history
        self.trail = deque(maxlen=20)
        self.pulse_phase = 0.0
        self.lost_frames = 0

    def draw(self, img, hand_landmarks, state, confidence):
        """
        Draw the HUD.
        :param img: Canvas
        :param hand_landmarks: MediaPipe landmarks
        :param state: Current Intent State
        :param confidence: Gesture Confidence (0-1)
        """
        if not hand_landmarks:
            self.lost_frames += 1
            # Only clear trail after sustained hand loss to prevent flicker
            if self.lost_frames > 8:
                self.trail.clear()
            return
            
        self.lost_frames = 0
        h, w, _ = img.shape
        
        # Center of palm (approx)
        idx_base = hand_landmarks[5] # Index MCP
        pinky_base = hand_landmarks[17] # Pinky MCP
        wrist = hand_landmarks[0]
        
        cx = int((idx_base.x + pinky_base.x + wrist.x) / 3 * w)
        cy = int((idx_base.y + pinky_base.y + wrist.y) / 3 * h)
        
        # Update Trail
        self.trail.appendleft((cx, cy))
        
        # 1. Draw Trail (Light Writer Effect)
        for i in range(1, len(self.trail)):
            thickness = int(np.sqrt(20 / i) * 2)
            cv2.line(img, self.trail[i-1], self.trail[i], config.COLOR_IDLE, thickness)

        # 2. Draw Reticle (Rotating Circles)
        self.pulse_phase += 0.1
        radius = int(40 + np.sin(self.pulse_phase) * 5)
        
        color = config.COLOR_IDLE
        if state == "MOVE":
             color = config.COLOR_MOVE
             radius = 20
        elif state == "CLICK_LEFT":
             color = config.COLOR_CLICK
             radius = 35
             cv2.circle(img, (cx, cy), radius, color, 3)
        elif state == "CLICK_RIGHT":
             color = config.COLOR_RIGHT_CLICK
             radius = 35
             cv2.putText(img, "R", (cx-10, cy+10), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        elif state == "DRAG_ACTIVE":
             color = config.COLOR_DRAG_ACTIVE
             radius = 35
             cv2.circle(img, (cx, cy), radius, color, 4) 
             # Lock icon
             cv2.rectangle(img, (cx-10, cy-10), (cx+10, cy+10), color, -1)
        elif state == "FIST":
             color = (0, 165, 255) # Orange
             radius = 30
             cv2.putText(img, "TOGGLE", (cx-25, cy-40), cv2.FONT_HERSHEY_PLAIN, 1, color, 1)

        elif state == "SCROLL":
             color = config.COLOR_SCROLL
             radius = 45
             # Draw arrows
             cv2.arrowedLine(img, (cx, cy - 20), (cx, cy - 60), color, 2)
             cv2.arrowedLine(img, (cx, cy + 20), (cx, cy + 60), color, 2)

        # Main Arc
        cv2.ellipse(img, (cx, cy), (radius, radius), 
                    self.pulse_phase * 50, 0, 270, color, 2)
        
        # Inner Tech Geometry (Decorations)
        if state == "CLICK_PENDING":
             # Draw bar indicating confidence
             bar_len = int(confidence * 100)
             cv2.line(img, (cx - 50, cy + 60), (cx - 50 + bar_len, cy + 60), color, 4)

        # 3. Text Label
        cv2.putText(img, f"STATUS: {state}", (cx + 50, cy - 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    def draw_cyber_skeleton(self, img, hand_landmarks, state="IDLE", draw_mode=False, sleep_mode=False):
        """
        Futuristic Holographic Cyber Skeleton Overlay.
        Strictly visual styling — renders glowing cybernetic bones, joints, and palm core.
        Pure visual enhancement: does not alter any mechanics or input handling.
        """
        if not hand_landmarks:
            return

        try:
            h, w, _ = img.shape
            pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks]

            # Dynamic Cyber Palettes
            if sleep_mode:
                bone_color = (0, 160, 220)       # Ambient amber-gold (sleep standby)
                joint_color = (180, 220, 255)
                core_color = (0, 120, 200)
                accent_color = (0, 180, 255)
            elif draw_mode:
                bone_color = (255, 230, 0)       # Holographic Neon Cyan
                joint_color = (255, 255, 255)    # White hot joint nodes
                core_color = (255, 200, 0)
                accent_color = (0, 255, 255)     # Laser Gold
            else:
                bone_color = (255, 210, 30)      # High-tech Electric Cyan
                joint_color = (255, 255, 255)
                core_color = (255, 180, 0)
                accent_color = (0, 255, 200)

            # 23 High-tech Bone Segments
            connections = [
                # Palm carpal frame & transversal arch
                (0, 1), (0, 5), (0, 17), (0, 9), (5, 9), (9, 13), (13, 17),
                # Thumb
                (1, 2), (2, 3), (3, 4),
                # Index
                (5, 6), (6, 7), (7, 8),
                # Middle
                (9, 10), (10, 11), (11, 12),
                # Ring
                (13, 14), (14, 15), (15, 16),
                # Pinky
                (17, 18), (18, 19), (19, 20)
            ]

            # 1. Render Bone Struts
            for p1_idx, p2_idx in connections:
                pt1 = pts[p1_idx]
                pt2 = pts[p2_idx]
                cv2.line(img, pt1, pt2, bone_color, 1, cv2.LINE_AA)

            # 2. Render Articulated Joint Nodes
            for idx, pt in enumerate(pts):
                if idx in (4, 8, 12, 16, 20):
                    # Fingertip Sensor Ring
                    cv2.circle(img, pt, 5, accent_color, 1, cv2.LINE_AA)
                    cv2.circle(img, pt, 2, (255, 255, 255), -1, cv2.LINE_AA)
                else:
                    # Joint node
                    cv2.circle(img, pt, 3, bone_color, 1, cv2.LINE_AA)
                    cv2.circle(img, pt, 1, (255, 255, 255), -1, cv2.LINE_AA)

            # Special Reticle for Index Fingertip (Laser Pointer / Pen)
            cv2.circle(img, pts[8], 8, accent_color, 1, cv2.LINE_AA)

            # 3. Palm Cyber Core (Mini Arc-Reactor)
            # Centroid of wrist (0), index MCP (5), and pinky MCP (17)
            core_cx = (pts[0][0] + pts[5][0] + pts[17][0]) // 3
            core_cy = (pts[0][1] + pts[5][1] + pts[17][1]) // 3

            self.pulse_phase += 0.05
            core_r = int(14 + np.sin(self.pulse_phase * 2) * 2)

            # Inner solid energy emitter
            cv2.circle(img, (core_cx, core_cy), 4, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(img, (core_cx, core_cy), 7, core_color, 1, cv2.LINE_AA)

            # Rotating outer targeting arcs
            rot_deg = int((self.pulse_phase * 90) % 360)
            cv2.ellipse(img, (core_cx, core_cy), (core_r, core_r), rot_deg, 0, 70, accent_color, 1, cv2.LINE_AA)
            cv2.ellipse(img, (core_cx, core_cy), (core_r, core_r), rot_deg + 120, 0, 70, accent_color, 1, cv2.LINE_AA)
            cv2.ellipse(img, (core_cx, core_cy), (core_r, core_r), rot_deg + 240, 0, 70, accent_color, 1, cv2.LINE_AA)
        except Exception:
            pass
