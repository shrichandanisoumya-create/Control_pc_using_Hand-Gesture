# Project J.A.R.V.I.S (Gesture Interface V3)

> "I am not controlling a computer. The computer understands my intent."

A production-grade, sci-fi inspired hand gesture interface featuring physics-based cursors, intent prediction, and cinematic HUD visuals.

## Features
-   **Physics Cursor**: Momentum, friction, and "weight" for stable, jitter-free control.
-   **Intent Engine**: Confidence-based gesture detection (no accidental clicks).
-   **Cinematic HUD**: Real-time holographic overlay with finger trails and dynamic reticles.
-   **OneEuro Smoothing**: Professional-grade jitter reduction.
-   **Air-Canvas Desktop Overlay**: Full-screen transparent click-through holographic overlay floating seamlessly over all desktop apps (VS Code, Chrome, PDFs) with dual-layer Iron Man Neon Cyan strokes, hover reticles, and top HUD pills.
-   **Smart Geometric Auto-Shape Snap**: Automatically snaps hand-drawn sketches into clean mathematical Straight Lines, Circles, Triangles, and Rectangles when pausing at stroke end.
-   **Partial Finger Eraser**: 3-finger gesture with glowing circular neon ring to erase specific touching strokes without clearing the screen.
-   **Pro-Level Cursor Stability**: Adaptive velocity-EMA smoothing with micro-deadzones (2-3px) to eliminate hand tremors during precision pointing and neat writing.
-   **Stark Scanline Sweep Wipe**: Fast sci-fi laser sweep wipe across the screen.

## Setup
1.  **Install Requirements**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Ensure you have `mediapipe`, `opencv-python`, `numpy`, `pyautogui`, `pillow`)*

2.  **Download Model**:
    Ensure `hand_landmarker.task` is in the root directory.

3.  **Run**:
    ```bash
    python main_v3.py
    ```

## Controls & Gestures

### 1. Standard Mouse Mode (Default)
-   **Move Cursor**: Open Palm / Hand Up. The cursor moves with relative physics and adaptive tremor smoothing.
-   **Left Click**: Pinch **Thumb + Index**.
-   **Right Click**: Pinch **Thumb + Middle**.
-   **Scroll Mode**: Raise **Index + Middle Fingers** (Peace Sign) and move hand up/down.
-   **Drag & Drop**: Make a **Closed Fist** to toggle pick / drop.
-   **Safety Pause**: Auto-activates on hand loss or low FPS.
-   **Quit System**: Press **'Q'** on your keyboard.

### 2. Full-Screen Desktop Air-Canvas Mode
-   **Toggle Draw Mode ON / OFF (Strict Single Gesture)**:
    -   Make the **Rock Sign** (**Index + Pinky UP**, Middle + Ring curled down, Thumb tucked).
    -   Hold for **0.8 seconds** continuously (charging HUD progress indicator displayed).
    -   Enforces a **1.5-second cooldown** after toggle to completely eliminate accidental switching.
    -   *OS Protection*: Mouse clicks and cursor movement are suppressed while in Draw Mode to prevent accidental clicks on underlying windows.
-   **Draw / Write**:
    -   Raise **Index Finger ONLY**.
    -   Draws smooth, glowing dual-layer Iron Man Neon Cyan (`#00FFFF`) strokes directly across your desktop screen with active edge margins for effortless 4-corner reach.
-   **Hover / Lift Pen**:
    -   Raise **Index + Middle Fingers** (Peace Sign).
    -   Lifts the pen (stops drawing lines), resets coordinates, and projects a sleek cyan targeting reticle at your index fingertip.
-   **Partial Finger Eraser**:
    -   Raise **3 Fingers** (**Index + Middle + Ring UP**, Pinky down).
    -   Activates a glowing circular **Neon Eraser Ring** (radius ~30px) that erases only the specific strokes it touches.
-   **Smart Auto-Shape Snap**:
    -   Draw a rough **Straight Line, Circle, Triangle, or Rectangle** and pause your finger still for **0.8 seconds** (or lift pen on closed shape).
    -   The system automatically snaps and replaces your rough sketch with a crisp, glowing geometric shape! Freehand handwriting and curves remain untouched.
-   **Stark Scanline Wipe / Clear**:
    -   Make a **Closed Fist** held for **0.6 seconds** (or press **'C'** on keyboard).
    -   A glowing horizontal cyan laser beam sweeps down the screen, wiping all strokes clean.
-   **Save Screenshot**:
    -   Press **'S'** on keyboard to save a full-desktop screenshot with your drawings to the `drawings/` folder.

## Architecture (For Developers)
-   `core/`: Application orchestrator and mode state machines.
-   `perception/`: MediaPipe tracker, OneEuroFilter, and `AdaptiveSmoother` (velocity-adaptive EMA + micro-deadzone).
-   `intent/`: Intent engine and gesture classification.
-   `control/`: Relative physics cursor engine.
-   `drawing/`:
    -   `desktop_overlay.py`: Borderless transparent click-through Win32/Tkinter overlay, dual-glow renderer, eraser, HUD pills, and screenshot engine.
    -   `shape_recognizer.py`: Contour geometry analyzer (Line, Circle, Triangle, Rectangle snapping).
-   `ui/`: Cinematic HUD overlays.

---
*Senior HCI Engineering Project*
