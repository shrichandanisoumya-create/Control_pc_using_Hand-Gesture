# ==============================================================================
# PROJECT J.A.R.V.I.S — AI HAND GESTURE WORKSTATION
# AUTHOR / CREATOR: Soumya Shrichandani
# COPYRIGHT (C) 2026 SOUMYA SHRICHANDANI. ALL RIGHTS RESERVED.
# ==============================================================================

import cv2
import numpy as np
import time
import os
import datetime
from gesture_v3 import config

class AirCanvas:
    """
    Air-Canvas / Holographic Drawing Engine.
    Handles virtual canvas buffer, stroke rendering with anti-aliasing,
    interactive top toolbar with hover-selection, holographic glow merging,
    saving to drawings/ directory, and quick clearing.
    """
    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height
        self.canvas = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Stroke Tracking (previous coordinates)
        self.xp = 0
        self.yp = 0
        
        # Tools & Colors
        self.current_color = config.DEFAULT_DRAW_COLOR
        self.current_tool = "BRUSH" # "BRUSH" or "ERASER"
        self.brush_thickness = config.BRUSH_THICKNESS
        self.eraser_thickness = config.ERASER_THICKNESS
        
        # Toolbar layout
        self.toolbar_height = 80
        self.buttons = []
        self._init_toolbar()
        
        # Hover / Dwell selection
        self.hovered_btn_name = None
        self.dwell_start = None
        self.dwell_required = 0.4 # 0.4s dwell for Clear/Save to avoid accidental activation
        
        # Toast notifications
        self.toast_text = ""
        self.toast_expiry = 0.0
        
        # Ensure drawings folder exists
        self.drawings_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", config.DRAWINGS_DIR)
        os.makedirs(self.drawings_dir, exist_ok=True)

    def _init_toolbar(self):
        """Build responsive toolbar button layout across top screen width."""
        btn_defs = [
            {"name": "CYAN", "type": "color", "color": config.COLOR_NEON_CYAN, "label": "CYAN"},
            {"name": "RED", "type": "color", "color": config.COLOR_NEON_RED, "label": "RED"},
            {"name": "GREEN", "type": "color", "color": config.COLOR_NEON_GREEN, "label": "GREEN"},
            {"name": "YELLOW", "type": "color", "color": config.COLOR_NEON_YELLOW, "label": "YELLOW"},
            {"name": "ERASER", "type": "eraser", "color": config.COLOR_ERASER, "label": "ERASER"},
            {"name": "CLEAR", "type": "clear", "color": (0, 80, 255), "label": "CLEAR ALL"},
            {"name": "SAVE", "type": "save", "color": (255, 180, 0), "label": "SAVE [S]"},
        ]
        
        n = len(btn_defs)
        margin = 12
        spacing = 8
        avail_w = self.width - (2 * margin) - ((n - 1) * spacing)
        btn_w = max(90, avail_w // n)
        btn_h = self.toolbar_height - 16
        y1 = 8
        y2 = y1 + btn_h

        self.buttons = []
        for i, b in enumerate(btn_defs):
            x1 = margin + i * (btn_w + spacing)
            x2 = min(self.width - margin, x1 + btn_w)
            self.buttons.append({
                **b,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2
            })

    def check_resize(self, width, height):
        """Resize canvas if frame dimensions change, preserving existing drawing."""
        if width != self.width or height != self.height:
            if self.canvas is not None:
                self.canvas = cv2.resize(self.canvas, (width, height), interpolation=cv2.INTER_LINEAR)
            else:
                self.canvas = np.zeros((height, width, 3), dtype=np.uint8)
            self.width = width
            self.height = height
            self._init_toolbar()

    def reset_pen(self):
        """Reset previous stroke coordinates to prevent connecting lines when lifting finger."""
        self.xp = 0
        self.yp = 0

    def set_toast(self, message, duration=2.5):
        """Display a HUD notification badge for a limited duration."""
        self.toast_text = message
        self.toast_expiry = time.time() + duration

    def clear_canvas(self):
        """Instantly wipe the entire drawing board."""
        self.canvas[:] = 0
        self.reset_pen()
        self.set_toast("CANVAS CLEARED", 2.0)

    def save_drawing(self, current_frame=None):
        """Save the current artwork / composite as a PNG file in the drawings directory."""
        try:
            os.makedirs(self.drawings_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"air_canvas_{timestamp}.png"
            filepath = os.path.join(self.drawings_dir, filename)

            if current_frame is not None:
                # Save composite: webcam feed + holographic glow drawing
                composite = self.render_holographic_overlay(current_frame.copy())
                cv2.imwrite(filepath, composite)
            else:
                # Save pure canvas drawing on dark background
                cv2.imwrite(filepath, self.canvas)

            self.set_toast(f"SAVED: {filename}", 3.0)
            return filepath
        except Exception as e:
            self.set_toast(f"SAVE ERROR: {str(e)}", 3.0)
            return None

    def draw_stroke(self, x1, y1):
        """
        Draw a continuous anti-aliased line from (xp, yp) to (x1, y1).
        Supports neon brush or eraser.
        """
        if self.xp == 0 and self.yp == 0:
            self.xp, self.yp = x1, y1

        if self.current_tool == "BRUSH":
            # Draw line with rounded endpoints for smooth strokes
            cv2.line(self.canvas, (self.xp, self.yp), (x1, y1), 
                     self.current_color, self.brush_thickness, cv2.LINE_AA)
            cv2.circle(self.canvas, (x1, y1), max(1, self.brush_thickness // 2), 
                       self.current_color, -1, cv2.LINE_AA)
        elif self.current_tool == "ERASER":
            # Eraser draws black (0, 0, 0) onto canvas to clear pixels
            cv2.line(self.canvas, (self.xp, self.yp), (x1, y1), 
                     (0, 0, 0), self.eraser_thickness, cv2.LINE_AA)
            cv2.circle(self.canvas, (x1, y1), max(1, self.eraser_thickness // 2), 
                       (0, 0, 0), -1, cv2.LINE_AA)

        self.xp, self.yp = x1, y1

    def handle_hover(self, x1, y1, current_frame=None):
        """
        Handle Hover / Peace Sign interaction over top toolbar buttons.
        Selects colors and tools, or triggers clear / save with dwell check.
        """
        self.reset_pen() # Pen is up when hovering

        # Check if index fingertip is inside toolbar region
        if y1 > self.toolbar_height:
            self.hovered_btn_name = None
            self.dwell_start = None
            return

        current_time = time.time()
        hovered_btn = None
        for btn in self.buttons:
            if btn["x1"] <= x1 <= btn["x2"] and btn["y1"] <= y1 <= btn["y2"]:
                hovered_btn = btn
                break

        if hovered_btn is None:
            self.hovered_btn_name = None
            self.dwell_start = None
            return

        btn_name = hovered_btn["name"]
        btn_type = hovered_btn["type"]

        # Track dwell time for this button
        if self.hovered_btn_name != btn_name:
            self.hovered_btn_name = btn_name
            self.dwell_start = current_time

        dwell_elapsed = current_time - self.dwell_start

        # Color & Eraser tools trigger immediately for snappy response
        if btn_type == "color":
            self.current_tool = "BRUSH"
            self.current_color = hovered_btn["color"]
            self.set_toast(f"COLOR: {btn_name}", 1.0)
        elif btn_type == "eraser":
            self.current_tool = "ERASER"
            self.set_toast("TOOL: ERASER", 1.0)
        elif btn_type == "clear":
            # Require 0.4s dwell so moving across toolbar doesn't accidentally wipe canvas
            if dwell_elapsed >= self.dwell_required:
                self.clear_canvas()
                self.dwell_start = current_time + 1.0 # Debounce
        elif btn_type == "save":
            if dwell_elapsed >= self.dwell_required:
                self.save_drawing(current_frame)
                self.dwell_start = current_time + 1.5 # Debounce

    def render_toolbar(self, img, hover_point=None):
        """Render sleek semi-transparent top header bar with futuristic buttons and hover effects."""
        h, w, _ = img.shape
        self.check_resize(w, h)

        # 1. Semi-transparent backdrop bar
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (w, self.toolbar_height), (15, 18, 24), -1)
        cv2.line(overlay, (0, self.toolbar_height), (w, self.toolbar_height), (40, 60, 80), 2)
        cv2.addWeighted(overlay, 0.75, img, 0.25, 0, img)

        current_time = time.time()
        hx, hy = hover_point if hover_point is not None else (-1, -1)

        for btn in self.buttons:
            x1, y1, x2, y2 = btn["x1"], btn["y1"], btn["x2"], btn["y2"]
            b_name = btn["name"]
            b_type = btn["type"]
            b_color = btn["color"]

            is_hovered = (x1 <= hx <= x2 and y1 <= hy <= y2)
            is_active = (b_type == "color" and self.current_tool == "BRUSH" and self.current_color == b_color) or \
                        (b_type == "eraser" and self.current_tool == "ERASER")

            # Button background fill
            if is_hovered:
                cv2.rectangle(img, (x1, y1), (x2, y2), (45, 55, 75), -1)
            elif is_active:
                cv2.rectangle(img, (x1, y1), (x2, y2), (30, 40, 55), -1)
            else:
                cv2.rectangle(img, (x1, y1), (x2, y2), (22, 26, 34), -1)

            # Border
            border_color = (80, 100, 120)
            border_thick = 1
            if is_active:
                border_color = b_color if b_type != "eraser" else (220, 220, 220)
                border_thick = 2
            if is_hovered:
                border_color = (255, 255, 255)
                border_thick = 2

            cv2.rectangle(img, (x1, y1), (x2, y2), border_color, border_thick)

            # Dwell progress fill for Clear and Save
            if is_hovered and b_type in ("clear", "save") and self.dwell_start is not None:
                elapsed = max(0.0, current_time - self.dwell_start)
                prog = min(1.0, elapsed / self.dwell_required)
                prog_w = int((x2 - x1) * prog)
                if prog_w > 0:
                    cv2.rectangle(img, (x1, y2 - 4), (x1 + prog_w, y2), border_color, -1)

            # Color Swatch / Icon preview
            swatch_cx = x1 + 18
            swatch_cy = (y1 + y2) // 2
            if b_type == "color":
                cv2.circle(img, (swatch_cx, swatch_cy), 7, b_color, -1)
                cv2.circle(img, (swatch_cx, swatch_cy), 8, (255, 255, 255) if is_active else (50, 50, 50), 1)
            elif b_type == "eraser":
                cv2.rectangle(img, (swatch_cx - 6, swatch_cy - 6), (swatch_cx + 6, swatch_cy + 6), (200, 200, 200), -1)
            elif b_type == "clear":
                cv2.putText(img, "X", (swatch_cx - 5, swatch_cy + 5), cv2.FONT_HERSHEY_PLAIN, 1.1, (0, 80, 255), 2)
            elif b_type == "save":
                cv2.putText(img, "S", (swatch_cx - 5, swatch_cy + 5), cv2.FONT_HERSHEY_PLAIN, 1.1, (255, 180, 0), 2)

            # Label text
            text_x = swatch_cx + 14
            text_y = swatch_cy + 4
            text_color = (240, 240, 240) if (is_hovered or is_active) else (160, 160, 160)
            cv2.putText(img, btn["label"], (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.40, text_color, 1, cv2.LINE_AA)

            # Active indicator pip on top border
            if is_active:
                cv2.line(img, (x1 + 4, y1 + 1), (x2 - 4, y1 + 1), border_color, 2)

    def render_holographic_overlay(self, img):
        """
        Merge drawing canvas onto video frame with glowing holographic neon effect.
        Non-drawn areas remain 100% untouched; drawn areas feature neon glow with semi-transparency.
        """
        h, w, _ = img.shape
        self.check_resize(w, h)

        # Quick check: if canvas has no pixels, return original frame
        gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        if not np.any(gray > 0):
            return img

        # Threshold mask of drawn strokes
        _, mask = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)

        # Generate ethereal neon glow via Gaussian blur
        glow = cv2.GaussianBlur(self.canvas, (15, 15), 0)
        neon_lines = cv2.addWeighted(self.canvas, 0.85, glow, 0.50, 0)

        # Cutout background and foreground areas
        img_bg = cv2.bitwise_and(img, img, mask=mask_inv)
        img_fg = cv2.bitwise_and(img, img, mask=mask)

        # Holographic composition: video feed shines through behind neon strokes
        blended_strokes = cv2.addWeighted(img_fg, 0.28, neon_lines, 0.95, 0)
        return cv2.add(img_bg, blended_strokes)

    def render_hud(self, img, draw_state, tip_point=None, toggle_progress=0.0):
        """
        Futuristic HUD overlays:
        - Mode & State Banner ("MODE: AIR CANVAS (DRAWING)")
        - Active Tool & Color Indicators
        - Dynamic Cursor Reticle (Pen Tip, Eraser Radius, Hover Target)
        - Bottom Quick-Help Guide
        - Notifications / Toasts
        """
        h, w, _ = img.shape

        # 1. Top Status Banner (Below Toolbar)
        banner_y = self.toolbar_height + 26
        
        # Mode Tag
        cv2.putText(img, "MODE: AIR CANVAS (DRAWING)", (20, banner_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2, cv2.LINE_AA)

        # State Tag
        state_color = (200, 200, 200)
        state_str = draw_state
        if draw_state == "DRAWING":
            state_color = self.current_color if self.current_tool == "BRUSH" else (220, 220, 220)
            state_str = f"DRAWING ({'BRUSH' if self.current_tool == 'BRUSH' else 'ERASER'})"
        elif draw_state == "HOVER":
            state_color = (255, 220, 0)
            state_str = "HOVER / TOOL SELECTION"
        elif draw_state == "CLEAR":
            state_color = (0, 80, 255)
            state_str = "QUICK CLEAR (FIST)"

        cv2.putText(img, f"|  {state_str}", (340, banner_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, state_color, 1, cv2.LINE_AA)

        # Active Tool Badge (Right Side)
        tool_label = f"TOOL: {self.current_tool}"
        if self.current_tool == "BRUSH":
            cv2.circle(img, (w - 180, banner_y - 6), 6, self.current_color, -1)
            cv2.putText(img, tool_label, (w - 165, banner_y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.50, (220, 220, 220), 1, cv2.LINE_AA)
        else:
            cv2.rectangle(img, (w - 185, banner_y - 12), (w - 173, banner_y), (200, 200, 200), -1)
            cv2.putText(img, tool_label, (w - 165, banner_y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.50, (220, 220, 220), 1, cv2.LINE_AA)

        # 2. Dynamic Cursor Reticle
        if tip_point is not None:
            tx, ty = tip_point
            if draw_state == "DRAWING":
                if self.current_tool == "BRUSH":
                    # Glowing neon pointer
                    cv2.circle(img, (tx, ty), max(2, self.brush_thickness // 2), self.current_color, -1)
                    cv2.circle(img, (tx, ty), self.brush_thickness + 4, (255, 255, 255), 1, cv2.LINE_AA)
                else:
                    # Eraser boundary preview
                    cv2.circle(img, (tx, ty), self.eraser_thickness // 2, (200, 200, 200), 2, cv2.LINE_AA)
                    cv2.circle(img, (tx, ty), 3, (0, 80, 255), -1)
            elif draw_state == "HOVER":
                # High-tech peace/hover dual ring
                cv2.circle(img, (tx, ty), 12, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.circle(img, (tx, ty), 20, (255, 220, 0), 1, cv2.LINE_AA)
                # Crosshairs
                cv2.line(img, (tx - 16, ty), (tx + 16, ty), (255, 220, 0), 1)
                cv2.line(img, (tx, ty - 16), (tx, ty + 16), (255, 220, 0), 1)

        # 3. Mode Toggle Hold Progress Indicator
        if toggle_progress > 0.0:
            cx, cy = w // 2, h // 2
            prog_radius = 50
            # Charging arc
            angle = int(toggle_progress * 360)
            cv2.ellipse(img, (cx, cy), (prog_radius, prog_radius), -90, 0, angle, (0, 255, 255), 4, cv2.LINE_AA)
            cv2.putText(img, f"EXITING AIR CANVAS: {int(toggle_progress * 100)}%", 
                        (cx - 130, cy + 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)

        # 4. Toast Notification Badge
        now = time.time()
        if self.toast_text and now < self.toast_expiry:
            tw = len(self.toast_text) * 11 + 40
            tx1 = (w - tw) // 2
            tx2 = tx1 + tw
            ty1 = h - 90
            ty2 = ty1 + 36

            overlay = img.copy()
            cv2.rectangle(overlay, (tx1, ty1), (tx2, ty2), (20, 25, 35), -1)
            cv2.addWeighted(overlay, 0.85, img, 0.15, 0, img)
            cv2.rectangle(img, (tx1, ty1), (tx2, ty2), (0, 255, 255), 1)
            cv2.putText(img, self.toast_text, (tx1 + 18, ty1 + 24), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

        # 5. Bottom Controls Guide Bar
        guide_y = h - 16
        guide_text = "[INDEX: DRAW]  [PEACE: HOVER/SELECT]  [FIST / 'C': CLEAR]  ['S': SAVE]  [ROCK / 4-FINGERS: EXIT]"
        cv2.putText(img, guide_text, (w // 2 - 340, guide_y), 
                    cv2.FONT_HERSHEY_PLAIN, 1.0, (180, 180, 180), 1, cv2.LINE_AA)
