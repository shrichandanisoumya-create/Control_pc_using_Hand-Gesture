# ==============================================================================
# PROJECT J.A.R.V.I.S — AI HAND GESTURE WORKSTATION
# AUTHOR / CREATOR: Soumya Shrichandani
# COPYRIGHT (C) 2026 SOUMYA SHRICHANDANI. ALL RIGHTS RESERVED.
# ==============================================================================

"""
Centralized source of truth for all physics, UI, and logic constants.
"""
import math
import pyautogui

# --- SYSTEM ---
APP_NAME = "J.A.R.V.I.S Gesture Interface"
AUTHOR = "Soumya Shrichandani"
COPYRIGHT = "Copyright (c) 2026 Soumya Shrichandani. All Rights Reserved."
WINDOW_WIDTH, WINDOW_HEIGHT = pyautogui.size()
TARGET_FPS = 60

# --- PERCEPTION (OneEuroFilter) ---
ONE_EURO_MIN_CUTOFF = 1.3   # Hz
ONE_EURO_BETA = 0.08
ONE_EURO_D_CUTOFF = 1.0     # Hz

# --- GESTURE CONFIG ---
GESTURE_CONFIDENCE_THRESHOLD = 0.8
CONFIDENCE_DECAY = 0.2
CONFIDENCE_GROWTH = 0.15

# --- AIR MOUSE PHYSICS ---
DEAD_ZONE = 0.002
BASE_SENSITIVITY = 3.0
ACCELERATION_FACTOR = 20.0
MAX_SENSITIVITY = 12.0
DELTA_SMOOTHING = 0.6

# --- GESTURES ---
PINCH_THRESHOLD_NORM = 0.06
CLICK_COOLDOWN = 0.4

# --- SCROLL ---
SCROLL_SPEED = 20
SCROLL_DEADZONE = 0.05

# --- DRAG ---
DRAG_TOGGLE_COOLDOWN = 1.0
COLOR_DRAG_ACTIVE = (0, 255, 0)

# --- UI COLORS (BGR) ---
COLOR_IDLE = (255, 255, 0)
COLOR_MOVE = (255, 255, 255)
COLOR_CLICK = (0, 0, 255)
COLOR_RIGHT_CLICK = (255, 0, 0)
COLOR_SCROLL = (255, 0, 255)
COLOR_TEXT = (255, 255, 255)

# --- SAFETY ---
FAILSAFE_FPS = 15

# --- SCREEN ---
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()

# --- AIR CANVAS COORDINATE MAPPING ---
# Active zone margins: amount to trim from each edge of the camera frame.
# 0.10 = 10% margin each side → user only needs to move hand in 80% of frame width/height.
# This gives natural, effort-free corner-to-corner desktop coverage.
CANVAS_MARGIN_X = 0.10
CANVAS_MARGIN_Y = 0.10

# --- MODE SWITCHING (Rock Sign) ---
DRAW_TOGGLE_HOLD_TIME = 0.8    # seconds of continuous hold to toggle
DRAW_TOGGLE_COOLDOWN  = 1.5    # post-toggle cooldown (seconds)

# --- PEN SMOOTHER (AdaptiveSmoother) ---
MICRO_DEADZONE_PIXELS = 1.5    # sub-pixel tremor lock (tighter than before)
SMOOTHER_BASE_ALPHA   = 0.55   # strong smoothing at rest
SMOOTHER_FAST_ALPHA   = 0.90   # snappy responsiveness during fast strokes

# --- DRAWING STYLE ---
COLOR_DRAW_LINE = "#00FFFF"    # Default Neon Cyan
LINE_WIDTH      = 6            # Crisp holographic thickness
OVERLAY_BG      = "#010101"    # Transparent color key

# --- ERASER ---
ERASER_RADIUS = 25

# --- FIST CLEAR (must hold continuously for this long) ---
FIST_CLEAR_HOLD_TIME = 0.8     # seconds (increased from 0.5 to prevent accidents)

# --- RADIAL COLOR WHEEL ---
RADIAL_TRIGGER_HOLD_TIME = 0.6  # seconds to hold Call Sign before wheel appears
RADIAL_DWELL_TIME        = 0.4  # seconds to hover a segment to select it
RADIAL_COLORS = [
    ("#00FFFF", "JARVIS CYAN"),
    ("#FF2A2A", "STARK RED"),
    ("#FFD700", "IRON GOLD"),
    ("#00FF66", "MATRIX GREEN"),
    ("#BF00FF", "HOLOGRAM PURPLE"),
]

# --- SAVE ---
DRAWINGS_DIR = "drawings"

# --- HUD COLORS (BGR for OpenCV) ---
COLOR_NEON_CYAN   = (255, 255, 0)
COLOR_NEON_RED    = (40, 40, 255)
COLOR_NEON_GREEN  = (40, 255, 40)
COLOR_NEON_YELLOW = (0, 255, 255)
COLOR_ERASER      = (180, 180, 180)
