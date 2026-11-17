# 🤖 J.A.R.V.I.S — AI Hand Gesture Workstation v3.4

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5.x-green?style=for-the-badge&logo=opencv&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Latest-orange?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Ultra--Smooth%20v3.4-brightgreen?style=for-the-badge)

**Control your entire PC with hand gestures — zero physical hardware required.**  
*An Iron Man / J.A.R.V.I.S-inspired desktop workstation featuring transparent Air-Canvas drawing, spline-smoothed handwriting, gesture sleep/wake control, and real-time HUD telemetry.*

[Key Features](#-key-features) • [Installation](#-installation--quick-start) • [Gesture Guide](#-complete-gesture-reference) • [Sleep Mode](#-sleep--standby-gesture) • [Colour Wheel & Controls](#-gta-v-radial-colour-wheel--quick-controls) • [Configuration](#-configuration--fine-tuning)

</div>

---

## ⚡ Overview

**J.A.R.V.I.S Gesture Workstation v3.4** turns any standard webcam into a high-precision, touchless computer interface. Featuring a multi-point **cubic B-spline drawing engine**, rotation-invariant finger tracking, dedicated **gesture sleep/standby mode**, and a latched **GTA V-style radial colour selector**, this workstation delivers silky smooth 30–60 FPS touchless desktop navigation.

---

## 🌟 Key Features

- 🖐️ **Rotation-Invariant Hand Tracking**: High-speed MediaPipe ML pipeline running at 60 FPS that tracks fingers regardless of hand tilt or angle.
- 💤 **Gesture Sleep / Wake Mode (NEW in v3.4)**: Hold a **Thumbs-Up** for 0.8s to put the workstation on standby (script keeps running, gestures freeze). Hold Thumbs-Up again to wake!
- 🎨 **Ultra-Smooth Air-Canvas**: Multi-point cubic spline interpolation creates fluid, organic handwriting with zero disjoint polygon stutter.
- 🎯 **Targeting Reticle**: Dynamic glowing cursor dot & crosshair continuously projects fingertip position with zero lag.
- 🎡 **Latched GTA V Radial Colour Wheel**: Summon via Call-Me sign (Thumb+Pinky); the wheel stays latched open so you can effortlessly point and lock any of the 5 holographic colours.
- ⌨️ **Instant Keyboard Colour Shortcuts**: Press keys `1`–`5` to instantly switch brush colours on the fly.
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

---

## 📦 Required Packages

```bash
pip install -r requirements.txt
```

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
git clone https://github.com/YourUsername/Control_pc_using_Hand-Gesture.git
cd Control_pc_using_Hand-Gesture
```

### 2. Create and Activate a Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify MediaPipe Model
Ensure `hand_landmarker.task` is located in the root directory. If missing, download it via PowerShell:
```powershell
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" -OutFile hand_landmarker.task
```

### 5. Launch the System
```bash
python main_v3.py
```

---

## ✋ Complete Gesture Reference

### 💤 Sleep / Standby Gesture (Universal)

| Gesture | Hand Pose | Action Triggered |
|:---|:---|:---|
| **Sleep / Wake** | 👍 **Thumbs-Up** (Thumb UP, 4 fingers curled — **Hold 0.45s**) | **Toggles Workstation Sleep Mode**<br>• In Sleep: Mouse & gestures freeze, script keeps running.<br>• To Wake: Hold Thumbs-Up again for 0.45s! |

---

### 🖱️ Normal Mode (Desktop Mouse Control)

| Gesture | Hand Pose | Action Triggered |
|:---|:---|:---|
| **Move Cursor** | 🖐️ **Open Palm** (All 5 fingers extended) | Cursor tracks hand movement with adaptive smoothing |
| **Left Click** | 👌 **Index Pinch** (Thumb tip touches Index tip) | Primary single click (0.4s cooldown) |
| **Right Click** | 🤏 **Middle Pinch** (Thumb tip touches Middle tip) | Context menu / Secondary click |
| **Scroll Mode** | ✌️ **Peace Sign** (Index + Middle extended, others curled) | Move hand UP to scroll up, DOWN to scroll down |
| **Drag & Drop** | ✊ **Closed Fist** | Toggles mouse drag lock (`mouseDown` / `mouseUp`) |
| **Air-Canvas Toggle**| 🤘 **Rock Sign** (Index + Pinky extended — **Hold 0.8s**) | **Enters Air-Canvas Drawing Mode** |

---

### 🎨 Air-Canvas Mode (Full-Screen Holographic Drawing)

| Gesture | Hand Pose | Action Triggered |
|:---|:---|:---|
| **Draw Stroke** | ☝️ **Index Extended** (Only index finger up) | Freehand smooth spline stroke with targeting reticle |
| **Hover / Aim** | ✌️ **Peace Sign** (Index + Middle extended) | Lifts pen; reveals dual-ring targeting reticle |
| **Mini Eraser** | 🤟 **Three Fingers** (Index + Middle + Ring up) | Circular eraser clearing strokes under fingertip |
| **Colour Wheel**| 🤙 **Call-Me Sign** (Thumb + Pinky — **Hold 0.35s**) | Latches open GTA V-style 5-colour selector |
| **Purge Canvas** | ✊ **Closed Fist** (All fingers curled — **Hold 0.8s**) | **Wipes entire canvas** (`CANVAS PURGED` banner) |
| **Exit Air-Canvas**| 🤘 **Rock Sign** (Index + Pinky — **Hold 0.8s**) | Closes overlay, returns to Normal Mode |

---

## 🎡 GTA V Radial Colour Wheel & Quick Controls

### 1. Gesture Wheel (Latched Mode)
Hold the **Call-Me Sign (Thumb + Pinky)** for 0.35s. The wheel opens and **stays latched open**!  
Point your index finger at any slice for **0.3 seconds** to lock the colour:

| Sector | Hex Value | Colour Name | Theme |
|:---:|:---:|:---:|:---:|
| 1 (Top) | `#00FFFF` | **JARVIS CYAN** | Arc Reactor cyan |
| 2 (Right) | `#FF2A2A` | **STARK RED** | Hot-rod armor crimson |
| 3 (Bottom-R) | `#FFD700` | **IRON GOLD** | Titanium gold alloy |
| 4 (Bottom-L) | `#00FF66` | **MATRIX GREEN** | Terminal neon green |
| 5 (Left) | `#BF00FF` | **HOLOGRAM PURPLE** | Quantum ultraviolet |

*Dismiss without choosing: close fist, show rock sign, or press `[Esc]`.*

### 2. Instant Keyboard Colour Keys
While in Air-Canvas Mode, switch colours instantly using your keyboard:
- `[ 1 ]` → **JARVIS Cyan** (`#00FFFF`)
- `[ 2 ]` → **Stark Red** (`#FF2A2A`)
- `[ 3 ]` → **Iron Gold** (`#FFD700`)
- `[ 4 ]` → **Matrix Green** (`#00FF66`)
- `[ 5 ]` → **Hologram Purple** (`#BF00FF`)
- `[ C ]` → **Canvas Purge** (Instant scanline wipe)
- `[ S ]` → **Save Artwork** (Exports PNG to `drawings/`)
- `[ Q ]` → **Master Quit**

---

## 🔧 Configuration & Fine-Tuning

Tweak settings inside `gesture_v3/config.py`:

```python
# Active Zone Mapping (effortless corner-to-corner screen reach)
CANVAS_MARGIN_X = 0.10          # 10% outer frame margin
CANVAS_MARGIN_Y = 0.10

# Sleep & Timing Thresholds
SLEEP_TOGGLE_HOLD_TIME   = 0.45 # Smooth & responsive hold time to Sleep/Wake
DRAW_TOGGLE_HOLD_TIME    = 0.8  # Seconds to hold Rock Sign to switch modes
FIST_CLEAR_HOLD_TIME     = 0.8  # Seconds to hold Fist to wipe canvas
RADIAL_TRIGGER_HOLD_TIME = 0.35 # Seconds to summon Colour Wheel
RADIAL_DWELL_TIME        = 0.30 # Seconds to hover over colour slice to lock

# Brush Appearance
COLOR_DRAW_LINE = "#00FFFF"    # Default Neon Cyan
LINE_WIDTH      = 6            # Drawing thickness (pixels)
ERASER_RADIUS   = 30           # Eraser disc radius (pixels)

# Anti-Tremor Smoother
MICRO_DEADZONE_PIXELS = 1.0    # Sub-pixel stillness lock
SMOOTHER_BASE_ALPHA   = 0.65   # Precision smoothing for handwriting
SMOOTHER_FAST_ALPHA   = 0.95   # Zero-lag responsiveness for fast strokes
```

---

<div align="center">

## 👨‍💻 Author & Credits

### **MADE BY - Soumya Shrichandani**
*Class 11 Developer & AI / Computer Vision Systems Engineer*

⭐ **Star this repository if you love futuristic computer vision interfaces!** ⭐

</div>
