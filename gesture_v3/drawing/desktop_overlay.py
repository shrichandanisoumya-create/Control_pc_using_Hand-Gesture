# ==============================================================================
# PROJECT J.A.R.V.I.S — AI HAND GESTURE WORKSTATION
# AUTHOR / CREATOR: Soumya Shrichandani
# COPYRIGHT (C) 2026 SOUMYA SHRICHANDANI. ALL RIGHTS RESERVED.
# ==============================================================================

"""
DesktopOverlay — Bulletproof transparent, click-through, full-screen Air-Canvas window.

Fixes applied (v3.2):
  [FIX 1]  Neon Cyan targeting reticle rendered at every fingertip position while
           Air-Canvas is active so the user always sees where they are pointing.
  [FIX 2]  Radial colour wheel: raycast / hover selection now works correctly.
           draw_color is updated immediately when a colour is locked; a "COLOR LOCKED"
           HUD pill confirms the selection before the wheel fades out.
  [FIX 3]  Strict fist-clear: auto-clear timers removed; canvas ONLY clears on an
           explicit 0.8 s fist hold (handled in system.py) or the 'C' key.
           clear_canvas() now shows "CANVAS PURGED" pill.

Includes:
  • Correct DWM transparency (applied after deiconify on live window)
  • Full-screen freehand drawing with LINE_WIDTH=6, ROUND caps, smooth=True
  • No auto-shape snapping (ShapeRecognizer never imported)
  • GTA-V style 5-colour holographic radial colour wheel
  • Strict fist-clear debounce (no auto-clear timers)
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
# Radial Color Wheel  [FIX 2 — hover selection now works correctly]
# ============================================================================
class RadialColorWheel:
    """
    GTA-V weapon-wheel style 5-segment holographic colour selector.
    Rendered entirely on the Tk canvas.

    FIX 2 changelog:
    - _segment_at() angle calculation is now stable across all screen quadrants.
    - update() resets dwell only when the segment genuinely changes (not every frame).
    - Confirmed colour is immediately applied to draw_color before hiding wheel.
    """
    COLORS     = config.RADIAL_COLORS   # list of (hex_color, label)
    N          = len(COLORS)
    RADIUS_OUT = 180    # px outer ring
    RADIUS_IN  = 60     # px inner dead-zone
    DWELL_TIME = config.RADIAL_DWELL_TIME   # 0.4 s

    def __init__(self, canvas: tk.Canvas, screen_w: int, screen_h: int):
        self.canvas   = canvas
        self.cx       = screen_w // 2
        self.cy       = screen_h // 2
        self.visible  = False
        self._items   = []          # canvas item ids for cleanup
        self._hovered = None        # currently hovered segment index
        self._dwell_start = None
        self._selected_color = None # hex color chosen

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def show(self):
        self.visible        = True
        self._hovered       = None
        self._dwell_start   = None
        self._selected_color = None
        self._draw()

    def hide(self):
        self.visible = False
        self._erase()
        self._hovered      = None
        self._dwell_start  = None

    def update(self, finger_x: int, finger_y: int) -> str | None:
        """
        Call every frame with the index fingertip position (screen coords).
        Returns the selected hex colour string when a selection is confirmed,
        or None while the user is still choosing.

        [FIX 2] Dwell timer now resets ONLY on genuine segment changes.
        """
        if not self.visible:
            return None

        seg = self._segment_at(finger_x, finger_y)

        if seg is None:
            # Cursor is in dead zone or outside wheel — reset dwell but keep
            # the last hovered segment highlighted so it doesn't flicker.
            if self._hovered is not None:
                self._hovered     = None
                self._dwell_start = None
                self._draw()
            return None

        # [FIX 2] Only reset the timer when the segment *actually* changes.
        if seg != self._hovered:
            self._hovered     = seg
            self._dwell_start = time.time()
            self._draw()
            return None

        # Same segment — advance dwell timer
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
        Return segment index (0..N-1) if (x,y) is within the wheel ring, else None.
        [FIX 2] atan2 result is normalised to [0, 360) correctly.
        """
        dx = x - self.cx
        dy = y - self.cy
        r  = math.hypot(dx, dy)
        if r < self.RADIUS_IN or r > self.RADIUS_OUT:
            return None
        # atan2 gives angle in (-180, 180]; shift to [0, 360)
        angle = (math.degrees(math.atan2(dy, dx)) + 360) % 360
        seg_size = 360.0 / self.N
        return int(angle / seg_size) % self.N

    # ------------------------------------------------------------------ #
    # Rendering
    # ------------------------------------------------------------------ #
    def _erase(self):
        self.canvas.delete("radial_wheel")

    def _draw(self, dwell_progress: float = 0.0):
        self._erase()
        if not self.visible:
            return

        seg_deg    = 360.0 / self.N
        rot_offset = -90  # start at 12-o'clock

        for i, (hex_color, label) in enumerate(self.COLORS):
            start_angle = rot_offset + i * seg_deg
            is_hovered  = (i == self._hovered)

            # Pulsing outer radius for hovered segment
            r_out = self.RADIUS_OUT + (12 if is_hovered else 0)
            r_in  = self.RADIUS_IN

            # Draw the arc slice using polygon approximation
            pts = self._arc_polygon(self.cx, self.cy, r_in, r_out,
                                     start_angle, seg_deg, steps=28)

            fill_color = hex_color
            outline_w  = 3 if is_hovered else 1
            self.canvas.create_polygon(
                pts, fill=fill_color,
                outline="#FFFFFF" if is_hovered else "#555555",
                width=outline_w,
                stipple="",          # solid fill
                tags="radial_wheel"
            )

            # Dwell progress arc (bright white partial ring on hovered slice)
            if is_hovered and dwell_progress > 0.0:
                self._draw_dwell_arc(start_angle, seg_deg, r_out, dwell_progress)

            # Label text
            mid_angle_rad = math.radians(start_angle + seg_deg / 2)
            lx = self.cx + math.cos(mid_angle_rad) * (r_in + (r_out - r_in) * 0.6)
            ly = self.cy + math.sin(mid_angle_rad) * (r_in + (r_out - r_in) * 0.6)
            font_size = 10 if is_hovered else 8
            self.canvas.create_text(
                lx, ly,
                text=label.replace(" ", "\n"),
                fill="#FFFFFF",
                font=("Consolas", font_size, "bold"),
                justify="center",
                tags="radial_wheel"
            )

        # Center dead-zone ring (dark circle)
        self.canvas.create_oval(
            self.cx - self.RADIUS_IN, self.cy - self.RADIUS_IN,
            self.cx + self.RADIUS_IN, self.cy + self.RADIUS_IN,
            fill="#050B14", outline="#00FFFF", width=2,
            tags="radial_wheel"
        )
        self.canvas.create_text(
            self.cx, self.cy,
            text="COLOR\nSELECT",
            fill="#00FFFF",
            font=("Consolas", 9, "bold"),
            justify="center",
            tags="radial_wheel"
        )

    def _draw_dwell_arc(self, start_angle: float, seg_deg: float,
                         r_out: float, progress: float):
        """White progress arc along outer edge of hovered segment."""
        arc_span = seg_deg * progress
        pts = self._arc_polygon(self.cx, self.cy,
                                 r_out - 6, r_out + 4,
                                 start_angle, arc_span, steps=20)
        self.canvas.create_polygon(
            pts, fill="#FFFFFF", outline="", tags="radial_wheel"
        )

    @staticmethod
    def _arc_polygon(cx: float, cy: float, r_in: float, r_out: float,
                      start_deg: float, span_deg: float, steps: int = 24) -> list:
        """
        Return a flat list of (x,y) coordinates forming a filled arc-wedge polygon
        (inner radius r_in, outer radius r_out, from start_deg for span_deg degrees).
        """
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
# Desktop Overlay
# ============================================================================
class DesktopOverlay:
    """
    Transparent, click-through, full-screen Air-Canvas overlay.

    Transparency: background = #010101 (config.OVERLAY_BG), registered as
    DWM colour key.  Drawing colour = #00FFFF — safely different from key.

    Lifecycle: __init__ → withdrawn.  show()/hide() on DRAW MODE toggle.
    update() must be called every frame to pump the Tk event loop.

    [FIX 1]  draw_stroke(), hover_reticle(), and erase_at() all render a
             Neon Cyan targeting reticle at the current fingertip so the user
             always has a precise crosshair / cursor dot on screen.
    [FIX 3]  clear_canvas() shows "CANVAS PURGED" and has NO auto-timer.
             It is ONLY called by explicit 0.8 s fist hold or 'C' key press.
    """

    # Neon reticle dimensions
    _RETICLE_INNER  = 6    # inner dot radius
    _RETICLE_OUTER  = 18   # outer ring radius
    _RETICLE_GAP    = 5    # crosshair gap from center
    _RETICLE_ARM    = 14   # crosshair arm length beyond outer ring
    _RETICLE_COLOR  = "#00FFFF"   # Neon Cyan
    _RETICLE_GLOW   = "#005F7F"   # darker glow halo

    def __init__(self):
        # ------------------------------------------------------------------ #
        # 1. Root window
        # ------------------------------------------------------------------ #
        self.root = tk.Tk()
        self.root.title("Jarvis_AirCanvas_Overlay")
        self.root.overrideredirect(True)

        self.width  = config.SCREEN_WIDTH
        self.height = config.SCREEN_HEIGHT
        self.root.geometry(f"{self.width}x{self.height}+0+0")

        self.bg_color = config.OVERLAY_BG  # "#010101"
        self.root.config(bg=self.bg_color)

        # ------------------------------------------------------------------ #
        # 2. Canvas
        # ------------------------------------------------------------------ #
        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg=self.bg_color,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill="both", expand=True)

        # ------------------------------------------------------------------ #
        # 3. Apply Win32 extended styles before first show
        #    (WS_EX_LAYERED must exist before -transparentcolor takes effect)
        # ------------------------------------------------------------------ #
        self.root.update_idletasks()
        try:
            hwnd = _get_toplevel_hwnd(self.root)
            _apply_ex_styles(hwnd)
        except Exception as e:
            print(f"[DesktopOverlay] Pre-show style warning: {e}")

        self.root.wm_attributes("-transparentcolor", self.bg_color)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-alpha", 1.0)

        # ------------------------------------------------------------------ #
        # 4. Start HIDDEN
        # ------------------------------------------------------------------ #
        self.is_visible = False
        self.root.withdraw()

        # ------------------------------------------------------------------ #
        # 5. Drawing state
        # ------------------------------------------------------------------ #
        self.xp = None
        self.yp = None
        self.draw_color = config.COLOR_DRAW_LINE  # active pen colour

        # ------------------------------------------------------------------ #
        # 6. HUD pill
        # ------------------------------------------------------------------ #
        self.pill_text   = ""
        self.pill_expiry = 0.0
        self.pill_color  = config.COLOR_DRAW_LINE

        # ------------------------------------------------------------------ #
        # 7. Radial wheel
        # ------------------------------------------------------------------ #
        self.radial_wheel = RadialColorWheel(self.canvas, self.width, self.height)

        # ------------------------------------------------------------------ #
        # 8. Save directory
        # ------------------------------------------------------------------ #
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
        """Show overlay — re-apply DWM transparency on the live window."""
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
        """Withdraw overlay — desktop is 100% unblocked."""
        if self.is_visible:
            self.lift_pen()
            self.hide_reticles()
            self.radial_wheel.hide()
            self.root.withdraw()
            self.is_visible = False

    # ======================================================================
    # Radial Wheel  [FIX 2]
    # ======================================================================

    def open_radial_wheel(self):
        """Show the GTA-V colour wheel."""
        if not self.radial_wheel.visible:
            self.radial_wheel.show()

    def close_radial_wheel(self):
        """Hide wheel without selecting."""
        if self.radial_wheel.visible:
            self.radial_wheel.hide()

    def update_radial_wheel(self, finger_x: int, finger_y: int) -> bool:
        """
        Feed the current fingertip position to the wheel.
        Returns True if a colour was just selected (and closes the wheel).

        [FIX 2] draw_color is immediately applied; pill says "COLOR LOCKED".
        """
        chosen = self.radial_wheel.update(finger_x, finger_y)
        if chosen is not None:
            # Immediately update the active drawing colour
            self.draw_color = chosen
            # Find human-readable label for HUD
            label = next(
                (lbl for col, lbl in config.RADIAL_COLORS if col == chosen),
                chosen
            )
            self.show_pill(f"COLOR LOCKED — {label}", color=chosen, duration=2.0)
            return True
        return False

    @property
    def radial_active(self) -> bool:
        return self.radial_wheel.visible

    # ======================================================================
    # Drawing tools  [FIX 1 — Neon Cyan targeting reticle on every tool]
    # ======================================================================

    def _draw_reticle(self, screen_x: int, screen_y: int,
                      mode: str = "draw") -> None:
        """
        Render a glowing Neon Cyan targeting reticle at (screen_x, screen_y).

        mode="draw"  → solid dot + outer ring + 4-arm crosshair
        mode="hover" → dual ring + 4-arm crosshair (no solid center)
        mode="erase" → dashed eraser-radius ring + center cross

        All items tagged "reticle" so hide_reticles() can wipe them atomically.
        """
        x, y = screen_x, screen_y
        tag  = "reticle"
        dc   = self.draw_color  # match current draw colour

        if mode == "draw":
            # 1. Glow halo (slightly larger, darker)
            g = self._RETICLE_OUTER + 4
            self.canvas.create_oval(
                x - g, y - g, x + g, y + g,
                outline=self._RETICLE_GLOW, width=4, tags=tag
            )
            # 2. Outer ring
            ro = self._RETICLE_OUTER
            self.canvas.create_oval(
                x - ro, y - ro, x + ro, y + ro,
                outline=dc, width=2, tags=tag
            )
            # 3. Solid center dot
            ri = self._RETICLE_INNER
            self.canvas.create_oval(
                x - ri, y - ri, x + ri, y + ri,
                fill=dc, outline="#FFFFFF", width=1, tags=tag
            )
            # 4. Crosshair arms (gap + arm length)
            gap = self._RETICLE_GAP
            arm = self._RETICLE_ARM + ro
            self.canvas.create_line(x - arm, y, x - gap, y,
                                    fill=dc, width=1, tags=tag)
            self.canvas.create_line(x + gap, y, x + arm, y,
                                    fill=dc, width=1, tags=tag)
            self.canvas.create_line(x, y - arm, x, y - gap,
                                    fill=dc, width=1, tags=tag)
            self.canvas.create_line(x, y + gap, x, y + arm,
                                    fill=dc, width=1, tags=tag)

        elif mode == "hover":
            # Double-ring targeting reticle (no fill dot)
            ro = self._RETICLE_OUTER
            self.canvas.create_oval(
                x - ro, y - ro, x + ro, y + ro,
                outline=dc, width=2, tags=tag
            )
            ri = ro - 8
            self.canvas.create_oval(
                x - ri, y - ri, x + ri, y + ri,
                outline="#FFFFFF", width=1, tags=tag
            )
            arm = self._RETICLE_ARM + ro
            gap = self._RETICLE_GAP
            self.canvas.create_line(x - arm, y, x - gap, y,
                                    fill="#FFD700", width=1, tags=tag)
            self.canvas.create_line(x + gap, y, x + arm, y,
                                    fill="#FFD700", width=1, tags=tag)
            self.canvas.create_line(x, y - arm, x, y - gap,
                                    fill="#FFD700", width=1, tags=tag)
            self.canvas.create_line(x, y + gap, x, y + arm,
                                    fill="#FFD700", width=1, tags=tag)

        elif mode == "erase":
            # Dashed eraser radius ring + small cross at center
            er = config.ERASER_RADIUS
            self.canvas.create_oval(
                x - er, y - er, x + er, y + er,
                outline="#C8C8C8", width=2, dash=(5, 4), tags=tag
            )
            self.canvas.create_line(x - 6, y, x + 6, y,
                                    fill="#FF4444", width=2, tags=tag)
            self.canvas.create_line(x, y - 6, x, y + 6,
                                    fill="#FF4444", width=2, tags=tag)

    def draw_stroke(self, screen_x: int, screen_y: int):
        """
        1-finger draw.  Uses current draw_color, LINE_WIDTH=6, ROUND caps.
        No shape snapping — pure freehand.

        [FIX 1] Renders Neon Cyan targeting reticle at current fingertip.
        """
        # Always delete old reticle & eraser ring first
        self.canvas.delete("reticle")
        self.canvas.delete("eraser_ring")

        # Draw the new stroke segment
        if self.xp is not None and self.yp is not None:
            dist = math.hypot(screen_x - self.xp, screen_y - self.yp)
            if dist >= 1.0:
                self.canvas.create_line(
                    self.xp, self.yp, screen_x, screen_y,
                    fill=self.draw_color,
                    width=config.LINE_WIDTH,   # 6
                    capstyle=tk.ROUND,
                    joinstyle=tk.ROUND,
                    smooth=True,
                    tags="drawing"
                )
        self.xp = screen_x
        self.yp = screen_y

        # [FIX 1] Render targeting reticle AFTER the stroke so it's on top
        self._draw_reticle(screen_x, screen_y, mode="draw")

    def lift_pen(self):
        self.xp = None
        self.yp = None

    def hover_reticle(self, screen_x: int, screen_y: int):
        """
        2-finger hover — pen lifted, hover reticle shown.

        [FIX 1] Replaced single-dot with full dual-ring targeting reticle.
        """
        self.lift_pen()
        self.canvas.delete("reticle")
        self.canvas.delete("eraser_ring")
        # Render the high-tech hover reticle
        self._draw_reticle(screen_x, screen_y, mode="hover")

    def erase_at(self, screen_x: int, screen_y: int, radius: int = config.ERASER_RADIUS):
        """
        3-finger eraser — circular erase zone.

        [FIX 1] Eraser-mode reticle shown at fingertip.
        """
        self.lift_pen()
        self.canvas.delete("reticle")
        self.canvas.delete("eraser_ring")

        x1, y1 = screen_x - radius, screen_y - radius
        x2, y2 = screen_x + radius, screen_y + radius

        # Erase overlapping strokes
        for item in self.canvas.find_overlapping(x1, y1, x2, y2):
            if "drawing" in self.canvas.gettags(item):
                self.canvas.delete(item)

        # [FIX 1] Eraser reticle (dashed ring + cross)
        self._draw_reticle(screen_x, screen_y, mode="erase")

    def clear_canvas(self):
        """
        Wipe all drawings.

        [FIX 3] ONLY called by explicit intent (fist 0.8 s hold or 'C' key).
        No auto-clear timers exist anywhere in the codebase.
        Shows "CANVAS PURGED" HUD pill on clear.
        """
        self.lift_pen()
        self.canvas.delete("all")
        self.show_pill("CANVAS PURGED", color="#FF4444", duration=2.0)

    def hide_reticles(self):
        self.canvas.delete("reticle")
        self.canvas.delete("eraser_ring")

    # ======================================================================
    # Save
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
        """'C' key alias — explicit keyboard clear."""
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

    # ======================================================================
    # Cleanup
    # ======================================================================

    def destroy(self):
        try:
            self.root.destroy()
        except Exception:
            pass
