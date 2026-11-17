# ==============================================================================
# PROJECT J.A.R.V.I.S — AI HAND GESTURE WORKSTATION
# AUTHOR / CREATOR: Soumya Shrichandani
# COPYRIGHT (C) 2026 SOUMYA SHRICHANDANI. ALL RIGHTS RESERVED.
# ==============================================================================

"""
Project J.A.R.V.I.S — Core Application Loop (V3.4 Sleep Mode & Precision Edition)
Orchestrates: Camera → Tracker → Smoother → Intent → Physics → UI → Display

New Features & Fixes in v3.4:
  • Custom Sleep / Wake Gesture (Thumbs-Up held 0.8s): freezes all input while keeping script running.
  • GTA V Radial Wheel Latching: stays open so index finger can effortlessly aim & pick colors.
  • Direct Keyboard Color Keys (1-5): instantly switch colors during Air-Canvas drawing.
  • Multi-point Spline Drawing: continuous fluid curves with zero segment stutter.
  • High-FPS pipeline with zero visual flicker.
"""

import cv2
import time
import numpy as np
from gesture_v3 import config
from gesture_v3.perception.tracker import HandTracker


class SystemController:
    """
    Main application loop and master state machine.
    """

    def __init__(self):
        self.running = True
        
        # High-speed camera capture with fallback
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(1)

        # Optimize camera pipeline: MJPG hardware decompression + 1-frame buffer for zero lag
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, config.TARGET_FPS)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.tracker = HandTracker()
        self.start_time = time.time()
        self.fps = float(config.TARGET_FPS)

        # ---------------------------------------------------------------- #
        # Sleep Mode State (Thumbs-Up Gesture)
        # ---------------------------------------------------------------- #
        self.sleep_mode = False
        self.sleep_toggle_start = None
        self.sleep_toggle_latched = False
        self.sleep_lost_frames = 0
        self.last_sleep_toggle_time = 0.0

        # ---------------------------------------------------------------- #
        # Air-Canvas State
        # ---------------------------------------------------------------- #
        self.draw_mode = False
        self.draw_toggle_start = None
        self.draw_toggle_latched = False
        self.last_draw_toggle_time = 0.0

        # Fist-clear state
        self.fist_clear_start = None
        self.fist_clear_latched = False
        self.fist_frame_count = 0
        self.FIST_CONFIRM_FRAMES = 8

        # Radial wheel state
        self.radial_trigger_start = None
        self.radial_trigger_latched = False

        # ---------------------------------------------------------------- #
        # Normal Mode State
        # ---------------------------------------------------------------- #
        self.drag_active = False
        self.last_toggle_time = 0.0
        self.last_click_time = 0.0

    # ==================================================================== #
    # Main loop
    # ==================================================================== #

    def run(self):
        print(f"[{config.APP_NAME}] Workstation Initialized | Developed by Soumya Shrichandani.")
        print("  • Thumbs-Up (Hold 0.45s): Sleep / Wake")
        print("  • Rock Sign (Hold 0.8s): Toggle Air-Canvas")
        print("  • Press 'Q' to Quit.\n")

        from gesture_v3.perception.smoothing import OneEuroFilter
        from gesture_v3.intent.classifier import GestureClassifier
        from gesture_v3.control.mouse_physics import PhysicsCursor
        from gesture_v3.ui.hud import CinematicHUD
        from gesture_v3.drawing.desktop_overlay import DesktopOverlay
        from gesture_v3.perception.adaptive_smoother import AdaptiveSmoother

        smoother = OneEuroFilter(time.time(), [0.5, 0.5],
                                 min_cutoff=config.ONE_EURO_MIN_CUTOFF,
                                 beta=config.ONE_EURO_BETA)
        classifier = GestureClassifier()
        cursor = PhysicsCursor()
        hud = CinematicHUD()
        overlay = DesktopOverlay()
        pen_smoother = AdaptiveSmoother()

        last_time = time.time()

        while self.running:
            # ------------------------------------------------------------ #
            # Timing & Anti-Flicker FPS Calculation
            # ------------------------------------------------------------ #
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            if dt > 0:
                instant_fps = 1.0 / dt
                self.fps = 0.90 * self.fps + 0.10 * instant_fps
            fps = self.fps

            # ------------------------------------------------------------ #
            # Camera read
            # ------------------------------------------------------------ #
            success, img = self.cap.read()
            if not success:
                continue

            img = cv2.flip(img, 1)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h_img, w_img = img.shape[:2]

            # ------------------------------------------------------------ #
            # Perception Pipeline
            # ------------------------------------------------------------ #
            frame_ts_ms = (current_time - self.start_time) * 1000.0
            detection_result = self.tracker.process(img_rgb, frame_ts_ms)

            hand_landmarks = None
            delta_x = delta_y = 0.0
            state = "IDLE"
            confidence = 0.0
            canvas_toggle_progress = 0.0
            sleep_toggle_progress = 0.0
            current_time_loop = time.time()

            if detection_result.hand_landmarks:
                hand_landmarks = detection_result.hand_landmarks[0]

                # Anchor point for relative cursor motion
                raw_point = hand_landmarks[5]
                norm_x, norm_y = raw_point.x, raw_point.y
                filtered_pos = smoother(current_time, [norm_x, norm_y])
                curr_x, curr_y = filtered_pos[0], filtered_pos[1]

                if hasattr(self, 'prev_hand_x'):
                    delta_x = curr_x - self.prev_hand_x
                    delta_y = curr_y - self.prev_hand_y
                self.prev_hand_x = curr_x
                self.prev_hand_y = curr_y

                # Intent classification
                state, meta = classifier.process(hand_landmarks)
                raw_state = state
                confidence = meta.get("confidence", 0.0)
                is_toggle_gesture = meta.get("is_toggle", False)
                is_call_sign = meta.get("is_call_sign", False)
                is_thumbs_up = meta.get("is_thumbs_up", False)
                is_fist = meta.get("is_fist", False)

                # Screen coordinate mapping for Air-Canvas
                raw_tip = hand_landmarks[8]
                tip_x = float(raw_tip.x)
                tip_y = float(raw_tip.y)

                mx = config.CANVAS_MARGIN_X
                my = config.CANVAS_MARGIN_Y

                clamped_x = max(mx, min(1.0 - mx, tip_x))
                clamped_y = max(my, min(1.0 - my, tip_y))
                raw_screen_x = (clamped_x - mx) / (1.0 - 2 * mx) * config.SCREEN_WIDTH
                raw_screen_y = (clamped_y - my) / (1.0 - 2 * my) * config.SCREEN_HEIGHT

                # Smooth screen coordinates for zero-jitter precision
                screen_x, screen_y = pen_smoother.update(raw_screen_x, raw_screen_y)

                # Pure Visual Hologram Skeleton Overlay (camera preview styling only)
                hud.draw_cyber_skeleton(img, hand_landmarks, state=state,
                                        draw_mode=self.draw_mode, sleep_mode=self.sleep_mode)

                # ======================================================== #
                # 1. SLEEP / WAKE GESTURE HANDLER (Thumbs-Up, Hold 0.45s)
                # ======================================================== #
                if is_thumbs_up:
                    self.sleep_lost_frames = 0
                    if self.sleep_toggle_start is None:
                        self.sleep_toggle_start = current_time_loop
                    elapsed_sleep = current_time_loop - self.sleep_toggle_start
                    sleep_toggle_progress = min(1.0, elapsed_sleep / config.SLEEP_TOGGLE_HOLD_TIME)

                    if (elapsed_sleep >= config.SLEEP_TOGGLE_HOLD_TIME
                            and not self.sleep_toggle_latched
                            and (current_time_loop - self.last_sleep_toggle_time) > config.SLEEP_TOGGLE_COOLDOWN):
                        self.sleep_mode = not self.sleep_mode
                        self.last_sleep_toggle_time = current_time_loop
                        self.sleep_toggle_latched = True
                        self.sleep_toggle_start = None
                        sleep_toggle_progress = 0.0

                        if self.sleep_mode:
                            if self.drag_active:
                                import pyautogui
                                pyautogui.mouseUp()
                                self.drag_active = False
                            overlay.lift_pen()
                            overlay.hide_reticles()
                            overlay.close_radial_wheel()
                            overlay.show_pill("SYSTEM SLEEP: ACTIVE", color="#FFD700", duration=2.5)
                        else:
                            overlay.show_pill("SYSTEM AWAKE: ACTIVE", color="#00FFFF", duration=2.0)
                else:
                    self.sleep_lost_frames += 1
                    if self.sleep_lost_frames > 4:
                        self.sleep_toggle_start = None
                        self.sleep_toggle_latched = False
                        sleep_toggle_progress = 0.0

                # ======================================================== #
                # 2. SLEEP MODE ACTIVE — FREEZE ALL INTERACTION
                # ======================================================== #
                if self.sleep_mode:
                    tool_state = "SLEEP (STANDBY)"
                    overlay.lift_pen()
                    overlay.hide_reticles()

                    # Sleep visuals on camera preview
                    cx_img, cy_img = w_img // 2, h_img // 2
                    cv2.circle(img, (cx_img, cy_img), 45, (0, 180, 255), 2, cv2.LINE_AA)
                    cv2.putText(img, "Z z Z", (cx_img - 22, cy_img + 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 255), 2, cv2.LINE_AA)
                    cv2.putText(img, "WORKSTATION IN SLEEP MODE",
                                (cx_img - 150, cy_img + 75),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 255), 2, cv2.LINE_AA)
                    cv2.putText(img, "SHOW THUMBS-UP (0.45s) TO WAKE UP",
                                (cx_img - 165, cy_img + 105),
                                cv2.FONT_HERSHEY_PLAIN, 1.1, (200, 200, 200), 1, cv2.LINE_AA)

                    # Show Wake-Up Progress Ring
                    if sleep_toggle_progress > 0.0:
                        prog_radius = 65
                        angle = int(sleep_toggle_progress * 360)
                        cv2.ellipse(img, (cx_img, cy_img), (prog_radius, prog_radius),
                                    -90, 0, angle, (0, 255, 0), 4, cv2.LINE_AA)
                        cv2.putText(img, f"WAKING UP: {int(sleep_toggle_progress * 100)}%",
                                    (cx_img - 90, cy_img - 80),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)

                # ======================================================== #
                # 3. WORKSTATION AWAKE — NORMAL / AIR-CANVAS INTERACTION
                # ======================================================== #
                else:
                    # Show sleep charging ring while holding thumbs-up
                    if sleep_toggle_progress > 0.0:
                        cx_img, cy_img = w_img // 2, h_img // 2
                        prog_radius = 55
                        angle = int(sleep_toggle_progress * 360)
                        cv2.ellipse(img, (cx_img, cy_img), (prog_radius, prog_radius),
                                    -90, 0, angle, (0, 220, 255), 4, cv2.LINE_AA)
                        cv2.putText(img, f"ENTERING SLEEP: {int(sleep_toggle_progress * 100)}%",
                                    (cx_img - 110, cy_img + 85),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 2, cv2.LINE_AA)

                    # --- Rock Sign Mode Toggle (Air-Canvas on/off) ---
                    if is_toggle_gesture and not overlay.radial_active:
                        if self.draw_toggle_start is None:
                            self.draw_toggle_start = current_time_loop
                        elapsed_draw = current_time_loop - self.draw_toggle_start
                        canvas_toggle_progress = min(1.0, elapsed_draw / config.DRAW_TOGGLE_HOLD_TIME)
                        overlay.update_pill_hold(canvas_toggle_progress)

                        if (elapsed_draw >= config.DRAW_TOGGLE_HOLD_TIME
                                and not self.draw_toggle_latched
                                and (current_time_loop - self.last_draw_toggle_time) > config.DRAW_TOGGLE_COOLDOWN):
                            self.draw_mode = not self.draw_mode
                            self.last_draw_toggle_time = current_time_loop
                            self.draw_toggle_latched = True
                            self.draw_toggle_start = None
                            canvas_toggle_progress = 0.0
                            pen_smoother.reset()

                            if self.draw_mode:
                                overlay.show()
                                overlay.show_pill("AIR CANVAS: ON", color="#00FFFF", duration=1.5)
                            else:
                                overlay.hide()

                            if self.drag_active:
                                import pyautogui
                                pyautogui.mouseUp()
                                self.drag_active = False
                    else:
                        self.draw_toggle_start = None
                        self.draw_toggle_latched = False

                    # ==================================================== #
                    # AIR CANVAS MODE
                    # ==================================================== #
                    if self.draw_mode:
                        tool_state = "IDLE"

                        # ─── Priority 1: Radial Wheel (LATCHED SELECTION) ───
                        if overlay.radial_active:
                            tool_state = "COLOR WHEEL"
                            overlay.lift_pen()
                            overlay.hide_reticles()

                            # Track user's finger aiming at the color slices
                            selected_col = overlay.update_radial_wheel(screen_x, screen_y)
                            if selected_col:
                                self.radial_trigger_latched = False
                                self.radial_trigger_start = None

                            # Allow closing wheel with Fist or Rock sign
                            if is_fist or is_toggle_gesture:
                                overlay.close_radial_wheel()

                        # ─── Priority 2: Triggering Radial Wheel (Call-Sign) ───
                        elif is_call_sign:
                            overlay.lift_pen()
                            overlay.hide_reticles()

                            if self.radial_trigger_start is None:
                                self.radial_trigger_start = current_time_loop
                            held_call = current_time_loop - self.radial_trigger_start

                            if (held_call >= config.RADIAL_TRIGGER_HOLD_TIME and not self.radial_trigger_latched):
                                overlay.open_radial_wheel()
                                self.radial_trigger_latched = True
                                tool_state = "COLOR WHEEL"

                        else:
                            self.radial_trigger_start = None
                            self.radial_trigger_latched = False

                            # ─── Priority 3: Eraser (3 Fingers) ───
                            if meta.get("is_eraser", False):
                                overlay.erase_at(screen_x, screen_y, radius=config.ERASER_RADIUS)
                                tool_state = "ERASER (3-FINGER)"

                            # ─── Priority 4: Hover / Navigate (Peace Sign) ───
                            elif meta.get("is_hover", False):
                                overlay.hover_reticle(screen_x, screen_y)
                                tool_state = "HOVER (2-FINGER)"

                            # ─── Priority 5: Draw (Index Only) ───
                            elif meta.get("is_draw", False):
                                overlay.draw_stroke(screen_x, screen_y)
                                tool_state = "DRAWING (1-FINGER)"

                            # ─── Priority 6: Strict Fist → Clear ───
                            elif meta.get("is_fist", False):
                                overlay.lift_pen()
                                overlay.hide_reticles()
                                tool_state = "CLEAR_PENDING"

                                self.fist_frame_count += 1
                                if self.fist_frame_count >= self.FIST_CONFIRM_FRAMES:
                                    if self.fist_clear_start is None:
                                        self.fist_clear_start = current_time_loop

                                    held_fist = current_time_loop - self.fist_clear_start
                                    prog = min(1.0, held_fist / config.FIST_CLEAR_HOLD_TIME)
                                    bar_w = int(w_img * 0.4 * prog)
                                    bar_x = (w_img - int(w_img * 0.4)) // 2
                                    bar_y = h_img - 80
                                    cv2.rectangle(img, (bar_x, bar_y),
                                                  (bar_x + int(w_img * 0.4), bar_y + 14),
                                                  (40, 40, 40), -1)
                                    cv2.rectangle(img, (bar_x, bar_y),
                                                  (bar_x + bar_w, bar_y + 14),
                                                  (0, 80, 255), -1)
                                    cv2.putText(img,
                                        f"HOLD TO CLEAR: {int(prog * 100)}%",
                                        (bar_x, bar_y - 6),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 80, 255), 1)

                                    if (held_fist >= config.FIST_CLEAR_HOLD_TIME and not self.fist_clear_latched):
                                        overlay.clear_canvas()
                                        self.fist_clear_latched = True
                                        tool_state = "CANVAS_CLEARED"

                            else:
                                overlay.lift_pen()
                                overlay.hide_reticles()

                        if not meta.get("is_fist", False):
                            self.fist_frame_count = 0
                            self.fist_clear_start = None
                            self.fist_clear_latched = False

                        # Camera HUD for Air-Canvas
                        cv2.putText(img, "AIR CANVAS: ACTIVE (DESKTOP OVERLAY)",
                                    (20, 70), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.65, (255, 255, 0), 2, cv2.LINE_AA)
                        cv2.putText(img, f"TOOL: {tool_state}  |  KEYS [1-5]: Colors",
                                    (20, 98), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.50, (200, 255, 255), 1, cv2.LINE_AA)
                        cv2.putText(img, "1-FINGER:Draw  2-FINGER:Hover  3-FINGER:Erase  THUMB+PINKY:Wheel  FIST:Clear",
                                    (20, 125), cv2.FONT_HERSHEY_PLAIN,
                                    0.95, (180, 180, 180), 1, cv2.LINE_AA)

                    # ==================================================== #
                    # NORMAL MOUSE MODE
                    # ==================================================== #
                    else:
                        if state == "FIST" and not is_thumbs_up and sleep_toggle_progress == 0.0:
                            if (current_time_loop - self.last_toggle_time > config.DRAG_TOGGLE_COOLDOWN):
                                self.drag_active = not self.drag_active
                                self.last_toggle_time = current_time_loop
                                import pyautogui
                                if self.drag_active:
                                    pyautogui.mouseDown()
                                else:
                                    pyautogui.mouseUp()

                        if self.drag_active:
                            state = "DRAG_ACTIVE"
                            if raw_state in ("MOVE", "IDLE", "FIST"):
                                cursor.update_relative(delta_x, delta_y, dt)
                        else:
                            if state == "MOVE":
                                cursor.update_relative(delta_x, delta_y, dt)

                            elif state == "CLICK_LEFT":
                                if (current_time_loop - self.last_click_time > config.CLICK_COOLDOWN):
                                    import pyautogui
                                    pyautogui.click()
                                    self.last_click_time = current_time_loop
                                    cv2.circle(img,
                                        (int(norm_x * w_img), int(norm_y * h_img)),
                                        50, config.COLOR_CLICK, 4)

                            elif state == "CLICK_RIGHT":
                                if (current_time_loop - self.last_click_time > config.CLICK_COOLDOWN):
                                    import pyautogui
                                    pyautogui.rightClick()
                                    self.last_click_time = current_time_loop

                            elif state == "SCROLL":
                                if hasattr(self, 'last_scroll_y'):
                                    dy = norm_y - self.last_scroll_y
                                    if abs(dy) > 0.005:
                                        import pyautogui
                                        scroll_amount = int(-dy * config.SCROLL_SPEED * 100)
                                        pyautogui.scroll(scroll_amount)
                                self.last_scroll_y = norm_y
                            else:
                                if hasattr(self, 'last_scroll_y'):
                                    del self.last_scroll_y

                        hud.draw(img, hand_landmarks, state, confidence)

                        # Mode switch ring
                        if canvas_toggle_progress > 0.0:
                            cx_img, cy_img = w_img // 2, h_img // 2
                            prog_radius = 50
                            angle = int(canvas_toggle_progress * 360)
                            cv2.ellipse(img, (cx_img, cy_img), (prog_radius, prog_radius),
                                        -90, 0, angle, (0, 255, 255), 4, cv2.LINE_AA)
                            cv2.putText(img, f"ENTERING CANVAS: {int(canvas_toggle_progress * 100)}%",
                                        (cx_img - 130, cy_img + 85),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)

            else:
                # Hand lost cleanup
                if self.drag_active:
                    import pyautogui
                    pyautogui.mouseUp()
                    self.drag_active = False

                if hasattr(self, 'prev_hand_x'):
                    del self.prev_hand_x
                    del self.prev_hand_y

                overlay.lift_pen()
                overlay.hide_reticles()
                pen_smoother.reset()

                self.draw_toggle_start = None
                self.draw_toggle_latched = False
                self.sleep_lost_frames += 1
                if self.sleep_lost_frames > 4:
                    self.sleep_toggle_start = None
                    self.sleep_toggle_latched = False
                self.fist_clear_start = None
                self.fist_clear_latched = False
                self.fist_frame_count = 0
                self.radial_trigger_start = None
                self.radial_trigger_latched = False

                if not self.draw_mode and not self.sleep_mode:
                    classifier.process(None)
                    hud.draw(img, None, "IDLE", 0.0)

            # ------------------------------------------------------------ #
            # System Info & HUD Telemetry
            # ------------------------------------------------------------ #
            fps_val = int(round(fps))
            fps_color = (0, 255, 0) if fps_val >= 25 else ((0, 255, 255) if fps_val >= 18 else (0, 165, 255))
            status_tag = "SLEEPING" if self.sleep_mode else ("AIR CANVAS" if self.draw_mode else "MOUSE")
            cv2.putText(img, f"J.A.R.V.I.S  |  FPS: {fps_val}  |  [{status_tag}]",
                        (20, 30), cv2.FONT_HERSHEY_PLAIN, 1.2, fps_color, 1, cv2.LINE_AA)

            # High-efficiency in-place watermark band
            band_h = 56
            band_y = h_img - band_h
            band_roi = img[band_y:h_img, 0:w_img]
            dark_tint = np.full_like(band_roi, (8, 10, 16))
            cv2.addWeighted(dark_tint, 0.70, band_roi, 0.30, 0, band_roi)

            # Accent line
            accent_col = (0, 180, 255) if self.sleep_mode else (0, 180, 180)
            cv2.line(img, (0, band_y), (w_img, band_y), accent_col, 1)

            # Watermark Lines
            mode_badge = "[ STANDBY / SLEEP ]" if self.sleep_mode else "[ SYSTEM ACTIVE ]"
            cv2.putText(img, mode_badge, (20, band_y + 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 255) if not self.sleep_mode else (0, 200, 255), 1, cv2.LINE_AA)
            cv2.putText(img, "MADE BY - Soumya Shrichandani", (20, band_y + 34),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (220, 220, 220), 1, cv2.LINE_AA)

            label_v3 = "AI WORKSTATION v3.4"
            (tw, _), _ = cv2.getTextSize(label_v3, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
            cv2.putText(img, label_v3, (w_img - tw - 20, band_y + 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 200, 180), 1, cv2.LINE_AA)

            # ------------------------------------------------------------ #
            # Display & Keyboard Event Handling
            # ------------------------------------------------------------ #
            cv2.imshow(config.APP_NAME, img)

            # Pump overlay event loop
            overlay.update()

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                self.running = False
            elif key in config.KEYBOARD_COLOR_MAP and self.draw_mode:
                # Instant color switch via keys 1, 2, 3, 4, 5
                hex_col, name = config.KEYBOARD_COLOR_MAP[key]
                overlay.set_active_color(hex_col, name)
            elif self.draw_mode:
                if key == ord('c') or key == ord('C'):
                    overlay.trigger_scanline_wipe()
                elif key == ord('s') or key == ord('S'):
                    overlay.save_artwork()
                elif key == 27:  # Esc key
                    if overlay.radial_active:
                        overlay.close_radial_wheel()

        overlay.destroy()
        self.cap.release()
        cv2.destroyAllWindows()
