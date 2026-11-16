# 🤖 J.A.R.V.I.S — AI Hand Gesture Workstation v3.0

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5.x-green?style=for-the-badge&logo=opencv&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Latest-orange?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Production--Ready-brightgreen?style=for-the-badge)

**Control your entire PC with hand gestures — zero physical hardware required.**  
*An Iron Man / J.A.R.V.I.S-inspired desktop workstation featuring transparent Air-Canvas drawing, physics-based mouse navigation, and real-time HUD telemetry.*

[Key Features](#-key-features) • [Installation](#-installation--quick-start) • [Gesture Guide](#-complete-gesture-reference) • [Configuration](#-configuration--fine-tuning) • [Troubleshooting](#-troubleshooting)

</div>

---

## ⚡ Overview

**J.A.R.V.I.S Gesture Workstation v3.0** transforms any standard webcam into a futuristic touchless computer interface. Built on high-performance computer vision algorithms, it offers seamless mouse control alongside a full-screen, holographic **Air-Canvas** overlay that lets you draw, write, erase, and select colours directly over your active desktop windows.

---

## 🌟 Key Features

- 🖐️ **21-Point Real-time Hand Tracking**: High-precision MediaPipe ML pipeline running at a fluid 60 FPS.
- 🖱️ **Physics-Based Cursor Engine**: Features inertia, acceleration, and adaptive deadzones for jitter-free, effortless precision cursor control.
- 🎨 **Holographic Air-Canvas**: Full-screen transparent desktop drawing engine powered by native Win32 DWM layered windows.
- 🎯 **Neon Cyan Targeting Reticle**: Dynamic glowing cursor dot & crosshair continuously projects fingertip position with zero lag.
- 🎡 **GTA V-Style Radial Colour Wheel**: 5-colour interactive selector activated via Call-Me sign with 0.4s dwell/hover selection.
- 🧹 **Anti-Accidental Clear Guard**: Strict closed-fist gesture with an 8-frame stability counter and 0.8s hold timer (`CANVAS PURGED`).
- 📷 **In-Feed HUD & Watermark**: Sleek cinematic telemetry overlay displaying real-time FPS, active tool state, and workstation credentials.
- 💾 **Instant Artwork Capture**: One-key high-resolution screenshot export directly to the `drawings/` directory.

---

## 🖥️ System Requirements

| Specification | Minimum | Recommended |
|:---|:---|:---|
| **Operating System** | Windows 10 (64-bit) | Windows 11 (64-bit) |
| **Python** | 3.10 | 3.11 / 3.12 / 3.13 |
| **Webcam** | 480p @ 30 FPS | 720p / 1080p @ 60 FPS |
| **RAM** | 4 GB | 8 GB+ |
| **Processor** | Dual-Core Intel/AMD | Quad-Core i5/Ryzen 5 or higher |
{Tested on Rysen 5 7000 series }
{needs an good webcamera}

> **Note**: Transparent click-through drawing overlay requires Windows Desktop Window Manager (DWM).

---

## 📦 Required Packages

| Library | Minimum Version | Purpose |
|:---|:---|:---|
| `opencv-python` | `>=4.8.0` | Camera capture, frame transformations & HUD overlay |
| `mediapipe` | `>=0.10.0` | ML landmark tracking (21 3D hand keypoints) |
| `pyautogui` | `>=0.9.54` | OS mouse dispatch & screenshot capture |
| `numpy` | `>=1.24.0` | Matrix math & image blend arrays |
| `pillow` | `>=9.5.0` | High-definition image manipulation & export |

---

## 🚀 Installation & Quick Start

### 1. Clone the Repository
```bash
git https://github.com/shrichandanisoumya-create/Control_pc_using_Hand-Gesture.git
cd Control_pc_using_Hand-Gesture
```

### 2. Create and Activate a Virtual Environment (Recommended)
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Required Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify MediaPipe Model
Ensure `hand_landmarker.task` is located in the root directory. If missing, fetch it via PowerShell:
```powershell
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" -OutFile hand_landmarker.task
```

### 5. Launch the System
```bash
python main_v3.py
```

---

## ✋ Complete Gesture Reference

### 🖱️ Normal Mode (Desktop Mouse Control)

| Gesture | Hand Pose | Action Triggered |
|:---|:---|:---|
| **Move Cursor** | 🖐️ **Open Palm** (All 5 fingers extended) | Cursor tracks hand movement with adaptive smoothing |
| **Left Click** | 👌 **Index Pinch** (Thumb tip touches Index tip) | Primary single click (0.4s cooldown) |
| **Right Click** | 🤏 **Middle Pinch** (Thumb tip touches Middle tip) | Context menu / Secondary click |
| **Scroll Mode** | ✌️ **Peace Sign** (Index + Middle extended, others curled) | Move hand UP to scroll up, DOWN to scroll down |
| **Drag & Drop** | ✊ **Closed Fist** | Toggles mouse drag lock (`mouseDown` / `mouseUp`) |
| **Air-Canvas Toggle**| 🤘 **Rock Sign** (Index + Pinky extended, hold 0.8s) | **Enters Air-Canvas Drawing Mode** |

---

### 🎨 Air-Canvas Mode (Full-Screen Holographic Overlay)

| Gesture | Hand Pose | Action Triggered |
|:---|:---|:---|
| **Draw Stroke** | ☝️ **Index Extended** (Only index finger up) | Freehand smooth neon stroke with targeting reticle |
| **Hover / Aim** | ✌️ **Peace Sign** (Index + Middle extended) | Lifts pen; reveals dual-ring targeting reticle |
| **Mini Eraser** | 🤟 **Three Fingers** (Index + Middle + Ring up) | Local circular eraser clearing strokes under fingertip |
| **Radial Colour Wheel**| 🤙 **Call-Me Sign** (Thumb + Pinky extended, hold 0.6s) | Pops up GTA V-style 5-colour selector |
| **Purge Canvas** | ✊ **Closed Fist** (All fingers curled, hold 0.8s) | **Wipes entire canvas** (`CANVAS PURGED` banner) |
| **Exit Air-Canvas**| 🤘 **Rock Sign** (Hold 0.8s) | Closes overlay, returns to Normal Mode |

---

### 🎡 GTA V Radial Colour Wheel Selection

When opening the colour wheel (**Thumb + Pinky**), hover your index fingertip over any sector for **0.4 seconds**:

| Sector | Hex Value | Colour Name | Theme |
|:---:|:---:|:---:|:---:|
| 1 | `#00FFFF` | **JARVIS CYAN** | Default Arc Reactor glow |
| 2 | `#FF2A2A` | **STARK RED** | Hot-rod armor crimson |
| 3 | `#FFD700` | **IRON GOLD** | Mark-III titanium alloy |
| 4 | `#00FF66` | **MATRIX GREEN** | Terminal neon green |
| 5 | `#BF00FF` | **HOLOGRAM PURPLE** | Quantum ultraviolet |

*Confirmation HUD flashes `"COLOR LOCKED — [COLOR NAME]"` upon successful selection.*

---

### ⌨️ Physical Keyboard Shortcuts

- `[ C ]` — **Instant Clear**: Triggers scanline wipe and clears all drawings.
- `[ S ]` — **Save Artwork**: Captures a full-resolution PNG to the `drawings/` folder.
- `[ Q ]` — **Master Exit**: Safely unhooks all Windows hooks, releases webcam, and exits.

---

## 🔧 Configuration & Fine-Tuning

Tweak settings directly inside `gesture_v3/config.py`:

```python
# Active Zone Mapping (removes deadzones & edge clipping)
CANVAS_MARGIN_X = 0.10          # 10% outer deadzone for full screen reach
CANVAS_MARGIN_Y = 0.10

# Gesture Thresholds & Timers
DRAW_TOGGLE_HOLD_TIME    = 0.8  # Seconds to hold Rock Sign to switch modes
FIST_CLEAR_HOLD_TIME     = 0.8  # Seconds to hold Fist to wipe canvas
RADIAL_TRIGGER_HOLD_TIME = 0.6  # Seconds to summon Colour Wheel
RADIAL_DWELL_TIME        = 0.4  # Seconds to hover over colour slice to lock

# Brush Appearance
COLOR_DRAW_LINE = "#00FFFF"    # Default Neon Cyan
LINE_WIDTH      = 6            # Drawing thickness
ERASER_RADIUS   = 25           # Eraser disc radius
```

---

## 🛠️ Troubleshooting

| Issue | Resolution |
|:---|:---|
| **Webcam Feed Blank** | Verify webcam index in `system.py` (`cv2.VideoCapture(0)` vs `(1)`). |
| **Laggy Cursor / Low FPS** | Ensure proper ambient lighting; close background GPU/CPU intensive tasks. |
| **Overlay Not Transparent** | Verify Windows DWM is active. Run Python command prompt with Administrator privileges if desktop restrictions exist. |
| **Canvas Auto-Clearing** | Make sure hand is fully visible; the strict 8-frame check requires steady fist posture before initiating clear countdown. |

---

## 📂 Project Architecture

```
Control_pc_using_Hand-Gesture-main/
├── main_v3.py                  # Workstation main launcher
├── hand_landmarker.task        # MediaPipe Vision Task model
├── requirements.txt            # Project dependencies
├── README.md                   # Documentation
└── gesture_v3/
    ├── config.py               # Central physics and UI configuration
    ├── core/
    │   └── system.py           # Core orchestrator loop & HUD watermark
    ├── control/
    │   └── mouse_physics.py    # Acceleration & friction physics
    ├── drawing/
    │   ├── desktop_overlay.py  # Transparent Win32 overlay & Reticle
    │   ├── air_canvas.py       # OpenCV drawing engine
    │   └── shape_recognizer.py # Shape identification
    ├── intent/
    │   └── classifier.py       # Gesture detection state machine
    ├── perception/
    │   ├── tracker.py          # MediaPipe task interface
    │   ├── adaptive_smoother.py# Dynamic EMA anti-jitter filter
    │   └── smoothing.py        # One-Euro filter
    └── ui/
        └── hud.py              # Cinematic HUD visuals
```

---

<div align="center">

## 👨‍💻 Author & Credits

### **MADE BY - Soumya Shrichandani**

⭐ **Star this repository if you love futuristic computer vision interfaces!** ⭐

</div>
