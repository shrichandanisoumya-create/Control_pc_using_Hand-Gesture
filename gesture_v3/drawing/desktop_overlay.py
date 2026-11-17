# ==============================================================================
# PROJECT J.A.R.V.I.S — AI HAND GESTURE WORKSTATION
# AUTHOR / CREATOR: Soumya Shrichandani
# COPYRIGHT (C) 2026 SOUMYA SHRICHANDANI. ALL RIGHTS RESERVED.
# ==============================================================================

"""
DesktopOverlay — Bulletproof transparent, click-through, full-screen Air-Canvas window.
Performance & Precision Edition (v3.4):
  • Multi-point spline interpolation for ultra-smooth, organic handwriting lines.
  • GTA V Radial Wheel with aligned hit-test sectors, visual targeting reticle, and latched mode.
  • Instant color switching via radial wheel or keyboard keys (1-5).
  • Zero-stutter rendering with optimized Tkinter item management.
"""

import tkinter as tk
import ctypes
import math
import time
import os
import datetime
import numpy as np
import pyautogui
from gesture_v3 import config

# ============================================================================
# Win32 constants & helpers
# ============================================================================
GWL_EXSTYLE       = -20
WS_EX_LAYERED     = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_NOACTIVATE  = 0x08000000
WS_EX_TOOLWINDOW  = 0x00000080
HWND_TOPMOST      = -1
SWP_NOSIZE        = 0x0001
SWP_NOMOVE        = 0x0002
SWP_NOACTIVATE    = 0x0010
TARGET_EX_STYLES  = WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW


def _get_toplevel_hwnd(root: tk.Tk) -> int:
    child  = root.winfo_id()
    parent = ctypes.windll.user32.GetParent(child)
    return parent if parent else child


def _apply_ex_styles(hwnd: int) -> None:
    cur = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, cur | TARGET_EX_STYLES)
    ctypes.windll.user32.SetWindowPos(
        hwnd, HWND_TOPMOST, 0, 0, 0, 0,
        SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE
    )


# ============================================================================
# Radial Color Wheel (Latched & Mathematically Aligned)
# ============================================================================
class RadialColorWheel:
    """
    GTA-V weapon-wheel style 5-segment holographic colour selector.
    Rendered entirely on the Tk canvas with precise hit-testing and aiming reticle.
    """
    COLORS     = config.RADIAL_COLORS   # list of (hex_color, label)
    N          = len(COLORS)
    RADIUS_OUT = config.RADIAL_OUTER_RADIUS      # 185 px
    RADIUS_IN  = config.RADIAL_DEADZONE_RADIUS   # 55 px
    DWELL_TIME = config.RADIAL_DWELL_TIME        # 0.3 s
    ROT_OFFSET = -90.0  # start at 12 o'clock

    def __init__(self, canvas: tk.Canvas, screen_w: int, screen_h: int):
        self.canvas   = canvas
        self.cx       = screen_w // 2
        self.cy       = screen_h // 2
        self.visible  = False
        self._hovered = None
        self._dwell_start = None
        self._aim_x = None
        self._aim_y = None

    def show(self):
        self.visible      = True
        self._hovered     = None
        self._dwell_start = None
        self._aim_x       = self.cx
        self._aim_y       = self.cy
        self._draw()

    def hide(self):
        self.visible = False
        self._erase()
        self._hovered     = None
        self._dwell_start = None

    def update(self, finger_x: int, finger_y: int) -> str | None:
        """
        Feed fingertip coordinates. Returns hex color string when selection is locked.
        """
        if not self.visible:
            return None

        self._aim_x = finger_x
        self._aim_y = finger_y
        seg = self._segment_at(finger_x, finger_y)

        if seg is None:
            if self._hovered is not None:
                self._hovered     = None
                self._dwell_start = None
                self._draw()
            else:
                self._draw()
            return None

        if seg != self._hovered:
            self._hovered     = seg
            self._dwell_start = time.time()
            self._draw()
            return None

        # Same segment — accumulate dwell timer
        if self._dwell_start is None:
            self._dwell_start = time.time()

        elapsed = time.time() - self._dwell_start
        progress = min(1.0, elapsed / self.DWELL_TIME)
        self._draw(dwell_progress=progress)

        if elapsed >= self.DWELL_TIME:
            chosen = self.COLORS[seg][0]
            self.hide()
            return chosen

        return None

    def _segment_at(self, x: int, y: int) -> int | None:
        """
        Hit-test sector calculation mathematically synchronized with visual rendering.
        """
        dx = x - self.cx
        dy = y - self.cy
        r  = math.hypot(dx, dy)
        if r < self.RADIUS_IN:
            return None
        # Angle relative to 12 o'clock (-90 deg)
        angle_math = math.degrees(math.atan2(dy, dx))
        angle_aligned = (angle_math - self.ROT_OFFSET + 360.0) % 360.0
        seg_size = 360.0 / self.N
        return int(angle_aligned / seg_size) % self.N

    def _erase(self):
        self.canvas.delete("radial_wheel")

    def _draw(self, dwell_progress: float = 0.0):
        self._erase()
        if not self.visible:
            return

        seg_deg = 360.0 / self.N

        # Outer background glow ring
        self.canvas.create_oval(
            self.cx - (self.RADIUS_OUT + 15), self.cy - (self.RADIUS_OUT + 15),
            self.cx + (self.RADIUS_OUT + 15), self.cy + (self.RADIUS_OUT + 15),
            fill="#050B14", outline="#003344", width=3, tags="radial_wheel"
        )

        for i, (hex_color, label) in enumerate(self.COLORS):
            start_angle = self.ROT_OFFSET + i * seg_deg
            is_hovered  = (i == self._hovered)

            r_out = self.RADIUS_OUT + (14 if is_hovered else 0)
            r_in  = self.RADIUS_IN

            pts = self._arc_polygon(self.cx, self.cy, r_in, r_out,
                                     start_angle, seg_deg, steps=28)

            self.canvas.create_polygon(
                pts, fill=hex_color,
                outline="#FFFFFF" if is_hovered else "#333333",
                width=3 if is_hovered else 1,
                tags="radial_wheel"
            )

            # Dwell progress arc
            if is_hovered and dwell_progress > 0.0:
                arc_span = seg_deg * dwell_progress
                arc_pts = self._arc_polygon(self.cx, self.cy,
                                             r_out - 8, r_out + 4,
                                             start_angle, arc_span, steps=20)
                self.canvas.create_polygon(
                    arc_pts, fill="#FFFFFF", outline="", tags="radial_wheel"
                )

            # Segment label
            mid_rad = math.radians(start_angle + seg_deg / 2)
            lx = self.cx + math.cos(mid_rad) * (r_in + (r_out - r_in) * 0.58)
            ly = self.cy + math.sin(mid_rad) * (r_in + (r_out - r_in) * 0.58)
            font_size = 10 if is_hovered else 8
            self.canvas.create_text(
                lx, ly,
                text=label.replace(" ", "\n"),
                fill="#FFFFFF" if is_hovered else "#EEEEEE",
                font=("Consolas", font_size, "bold"),
                justify="center",
                tags="radial_wheel"
            )

        # Center hub
        self.canvas.create_oval(
            self.cx - self.RADIUS_IN, self.cy - self.RADIUS_IN,
            self.cx + self.RADIUS_IN, self.cy + self.RADIUS_IN,
            fill="#050B14", outline="#00FFFF", width=2,
            tags="radial_wheel"
        )
        self.canvas.create_text(
            self.cx, self.cy,
            text="POINT TO\nCHOOSE",
            fill="#00FFFF",
            font=("Consolas", 8, "bold"),
            justify="center",
            tags="radial_wheel"
        )

        # Aiming pointer line & reticle
        if self._aim_x is not None and self._aim_y is not None:
            self.canvas.create_line(
                self.cx, self.cy, self._aim_x, self._aim_y,
                fill="#00FFFF", width=1, dash=(3, 3), tags="radial_wheel"
            )
            self.canvas.create_oval(
                self._aim_x - 8, self._aim_y - 8,
                self._aim_x + 8, self._aim_y + 8,
                fill="#FFFFFF", outline="#00FFFF", width=2, tags="radial_wheel"
            )

    @staticmethod
    def _arc_polygon(cx: float, cy: float, r_in: float, r_out: float,
                      start_deg: float, span_deg: float, steps: int = 24) -> list:
        pts = []
        for k in range(steps + 1):
            a = math.radians(start_deg + span_deg * k / steps)
            pts.append(cx + math.cos(a) * r_out)
            pts.append(cy + math.sin(a) * r_out)
        for k in range(steps, -1, -1):
            a = math.radians(start_deg + span_deg * k / steps)
            pts.append(cx + math.cos(a) * r_in)
            pts.append(cy + math.sin(a) * r_in)
        return pts


# ============================================================================
# Desktop Overlay (Ultra-Smooth Spline Drawing Engine)
# ============================================================================
class DesktopOverlay:
    """
    Transparent, click-through, full-screen Air-Canvas overlay with high-fidelity
    spline curve interpolation and zero-lag reticle feedback.
    """

    _RETICLE_INNER  = 6
    _RETICLE_OUTER  = 18
    _RETICLE_GAP    = 5
    _RETICLE_ARM    = 14
    _RETICLE_COLOR  = "#00FFFF"
    _RETICLE_GLOW   = "#005F7F"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Jarvis_AirCanvas_Overlay")
        self.root.overrideredirect(True)

        self.width  = config.SCREEN_WIDTH
        self.height = config.SCREEN_HEIGHT
        self.root.geometry(f"{self.width}x{self.height}+0+0")

        self.bg_color = config.OVERLAY_BG  # "#010101"
        self.root.config(bg=self.bg_color)

        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg=self.bg_color,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.root.update_idletasks()
        try:
            hwnd = _get_toplevel_hwnd(self.root)
            _apply_ex_styles(hwnd)
        except Exception as e:
            print(f"[DesktopOverlay] Pre-show style warning: {e}")

        self.root.wm_attributes("-transparentcolor", self.bg_color)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-alpha", 1.0)

        self.is_visible = False
        self.root.withdraw()

        # Continuous spline stroke tracking
        self.current_stroke_id  = None
        self.current_stroke_pts = []
        self.xp = None
        self.yp = None
        self.draw_color = config.COLOR_DRAW_LINE

        # HUD pill
        self.pill_text   = ""
        self.pill_expiry = 0.0
        self.pill_color  = config.COLOR_DRAW_LINE

        # Radial wheel
        self.radial_wheel = RadialColorWheel(self.canvas, self.width, self.height)

        # Save directory
        self.drawings_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", config.DRAWINGS_DIR)
        )
        try:
            os.makedirs(self.drawings_dir, exist_ok=True)
        except Exception:
            pass

    # ======================================================================
    # Visibility
    # ======================================================================

    def show(self):
        if not self.is_visible:
            self.root.deiconify()
            self.root.update_idletasks()
            self.root.update()
            try:
                hwnd = _get_toplevel_hwnd(self.root)
                _apply_ex_styles(hwnd)
            except Exception as e:
                print(f"[DesktopOverlay] show() style warning: {e}")
            self.root.wm_attributes("-transparentcolor", self.bg_color)
            self.root.wm_attributes("-topmost", True)
            self.root.wm_attributes("-alpha", 1.0)
            self.root.update_idletasks()
            self.is_visible = True

    def hide(self):
        if self.is_visible:
            self.lift_pen()
            self.hide_reticles()
            self.radial_wheel.hide()
            self.root.withdraw()
            self.is_visible = False

    # ======================================================================
    # Radial Wheel & Direct Color Control
    # ======================================================================

    def open_radial_wheel(self):
        if not self.radial_wheel.visible:
            self.radial_wheel.show()

    def close_radial_wheel(self):
        if self.radial_wheel.visible:
            self.radial_wheel.hide()

    def update_radial_wheel(self, finger_x: int, finger_y: int) -> bool:
        chosen = self.radial_wheel.update(finger_x, finger_y)
        if chosen is not None:
            self.draw_color = chosen
            label = next((lbl for col, lbl in config.RADIAL_COLORS if col == chosen), chosen)
            self.show_pill(f"COLOR LOCKED — {label}", color=chosen, duration=2.0)
            return True
        return False

    def set_active_color(self, hex_color: str, label: str = None):
        """Instant color switch via keyboard or direct call."""
        self.draw_color = hex_color
        if label is None:
            label = next((lbl for col, lbl in config.RADIAL_COLORS if col == hex_color), hex_color)
        self.show_pill(f"COLOR: {label}", color=hex_color, duration=1.5)

    @property
    def radial_active(self) -> bool:
        return self.radial_wheel.visible

    # ======================================================================
    # High-Fidelity Drawing Engine (Spline Curves & Anti-Stutter)
    # ======================================================================

    def _draw_reticle(self, screen_x: int, screen_y: int, mode: str = "draw") -> None:
        x, y = screen_x, screen_y
        tag  = "reticle"
        dc   = self.draw_color

        if mode == "draw":
            ro = self._RETICLE_OUTER
            ri = self._RETICLE_INNER
            self.canvas.create_oval(x - ro, y - ro, x + ro, y + ro, outline=dc, width=2, tags=tag)
            self.canvas.create_oval(x - ri, y - ri, x + ri, y + ri, fill=dc, outline="#FFFFFF", width=1, tags=tag)
            gap = self._RETICLE_GAP
            arm = self._RETICLE_ARM + ro
            self.canvas.create_line(x - arm, y, x - gap, y, fill=dc, width=1, tags=tag)
            self.canvas.create_line(x + gap, y, x + arm, y, fill=dc, width=1, tags=tag)
            self.canvas.create_line(x, y - arm, x, y - gap, fill=dc, width=1, tags=tag)
            self.canvas.create_line(x, y + gap, x, y + arm, fill=dc, width=1, tags=tag)

        elif mode == "hover":
            ro = self._RETICLE_OUTER
            ri = ro - 7
            self.canvas.create_oval(x - ro, y - ro, x + ro, y + ro, outline=dc, width=2, tags=tag)
            self.canvas.create_oval(x - ri, y - ri, x + ri, y + ri, outline="#FFFFFF", width=1, tags=tag)
            arm = self._RETICLE_ARM + ro
            gap = self._RETICLE_GAP
            self.canvas.create_line(x - arm, y, x - gap, y, fill="#FFD700", width=1, tags=tag)
            self.canvas.create_line(x + gap, y, x + arm, y, fill="#FFD700", width=1, tags=tag)
            self.canvas.create_line(x, y - arm, x, y - gap, fill="#FFD700", width=1, tags=tag)
            self.canvas.create_line(x, y + gap, x, y + arm, fill="#FFD700", width=1, tags=tag)

        elif mode == "erase":
            er = config.ERASER_RADIUS
            self.canvas.create_oval(x - er, y - er, x + er, y + er, outline="#C8C8C8", width=2, dash=(5, 4), tags=tag)
            self.canvas.create_line(x - 6, y, x + 6, y, fill="#FF4444", width=2, tags=tag)
            self.canvas.create_line(x, y - 6, x, y + 6, fill="#FF4444", width=2, tags=tag)

    def draw_stroke(self, screen_x: int, screen_y: int):
        """
        Continuous multi-point spline stroke rendering.
        Eliminates jagged polygon segments and creates smooth fluid handwriting.
        """
        self.canvas.delete("reticle")
        self.canvas.delete("eraser_ring")

        if self.current_stroke_id is None:
            # Start new continuous spline stroke
            self.current_stroke_pts = [screen_x, screen_y, screen_x + 0.1, screen_y + 0.1]
            self.current_stroke_id = self.canvas.create_line(
                self.current_stroke_pts,
                fill=self.draw_color,
                width=config.LINE_WIDTH,
                capstyle=tk.ROUND,
                joinstyle=tk.ROUND,
                smooth=True,
                splinesteps=12,
                tags="drawing"
            )
            self.xp = screen_x
            self.yp = screen_y
        else:
            dist = math.hypot(screen_x - self.xp, screen_y - self.yp)
            if dist >= 2.0:
                self.current_stroke_pts.extend([screen_x, screen_y])
                self.canvas.coords(self.current_stroke_id, *self.current_stroke_pts)
                self.xp = screen_x
                self.yp = screen_y

                # Bounded spline chunking: keeps each curve lightweight for continuous silky 60 FPS
                if len(self.current_stroke_pts) >= 12:
                    self.current_stroke_pts = [self.xp, self.yp, screen_x + 0.1, screen_y + 0.1]
                    self.current_stroke_id = self.canvas.create_line(
                        self.current_stroke_pts,
                        fill=self.draw_color,
                        width=config.LINE_WIDTH,
                        capstyle=tk.ROUND,
                        joinstyle=tk.ROUND,
                        smooth=True,
                        splinesteps=12,
                        tags="drawing"
                    )

        self._draw_reticle(screen_x, screen_y, mode="draw")

    def lift_pen(self):
        """Finalize current stroke segment."""
        self.current_stroke_id = None
        self.current_stroke_pts = []
        self.xp = None
        self.yp = None

    def hover_reticle(self, screen_x: int, screen_y: int):
        self.lift_pen()
        self.canvas.delete("reticle")
        self.canvas.delete("eraser_ring")
        self._draw_reticle(screen_x, screen_y, mode="hover")

    def erase_at(self, screen_x: int, screen_y: int, radius: int = config.ERASER_RADIUS):
        self.lift_pen()
        self.canvas.delete("reticle")
        self.canvas.delete("eraser_ring")

        x1, y1 = screen_x - radius, screen_y - radius
        x2, y2 = screen_x + radius, screen_y + radius

        for item in self.canvas.find_overlapping(x1, y1, x2, y2):
            if "drawing" in self.canvas.gettags(item):
                self.canvas.delete(item)

        self._draw_reticle(screen_x, screen_y, mode="erase")

    def clear_canvas(self):
        self.lift_pen()
        self.canvas.delete("drawing")
        self.canvas.delete("reticle")
        self.canvas.delete("eraser_ring")
        self.show_pill("CANVAS PURGED", color="#FF4444", duration=2.0)

    def hide_reticles(self):
        self.canvas.delete("reticle")
        self.canvas.delete("eraser_ring")

    # ======================================================================
    # Save & Quick Actions
    # ======================================================================

    def save_artwork(self):
        try:
            ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"air_canvas_{ts}.png"
            filepath = os.path.join(self.drawings_dir, filename)
            pyautogui.screenshot().save(filepath)
            self.show_pill("SCREENSHOT SAVED", color="#00FF88", duration=2.0)
            print(f"[AirCanvas] Saved: {filepath}")
            return filepath
        except Exception as e:
            self.show_pill("SAVE ERROR", color="#FF4444", duration=2.0)
            print(f"[AirCanvas] Save error: {e}")
            return None

    def trigger_scanline_wipe(self):
        self.clear_canvas()

    # ======================================================================
    # HUD Pill
    # ======================================================================

    def show_pill(self, text: str, color: str = config.COLOR_DRAW_LINE, duration: float = 1.5):
        self.pill_text   = text
        self.pill_color  = color
        self.pill_expiry = time.time() + duration
        self._render_hud_pill()

    def update_pill_hold(self, progress: float):
        if progress > 0.0:
            pct = int(progress * 100)
            self.pill_text   = f"AIR CANVAS: TOGGLING... ({pct}%)"
            self.pill_color  = "#FFD700" if pct < 80 else config.COLOR_DRAW_LINE
            self.pill_expiry = time.time() + 0.3
            self._render_hud_pill(progress=progress)

    def _render_hud_pill(self, progress: float = None):
        self.canvas.delete("hud_pill")
        if not self.pill_text or time.time() > self.pill_expiry:
            return
        pill_w = max(260, len(self.pill_text) * 11 + 40)
        pill_h = 34
        cx = self.width  // 2
        cy = 28
        x1, y1 = cx - pill_w // 2, cy - pill_h // 2
        x2, y2 = cx + pill_w // 2, cy + pill_h // 2
        self.canvas.create_rectangle(x1, y1, x2, y2,
            fill="#050B14", outline=self.pill_color, width=2, tags="hud_pill")
        dot_x = x1 + 18
        self.canvas.create_oval(dot_x - 4, cy - 4, dot_x + 4, cy + 4,
            fill=self.pill_color, outline="#FFFFFF", width=1, tags="hud_pill")
        self.canvas.create_text(cx + 8, cy,
            text=self.pill_text, fill="#FFFFFF",
            font=("Consolas", 11, "bold"), tags="hud_pill")
        if progress is not None and progress > 0.0:
            prog_w = int((x2 - x1) * progress)
            self.canvas.create_line(x1, y2 - 2, x1 + prog_w, y2 - 2,
                fill=self.pill_color, width=3, tags="hud_pill")

    # ======================================================================
    # Main-loop pump
    # ======================================================================

    def update(self):
        try:
            if self.is_visible:
                self._render_hud_pill()
            self.root.update_idletasks()
            self.root.update()
        except tk.TclError:
            pass

    def destroy(self):
        try:
            self.root.destroy()
        except Exception:
            pass
