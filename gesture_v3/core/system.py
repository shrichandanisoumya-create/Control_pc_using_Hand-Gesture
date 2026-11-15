# ==============================================================================
# PROJECT J.A.R.V.I.S — AI HAND GESTURE WORKSTATION
# AUTHOR / CREATOR: Soumya Shrichandani
# COPYRIGHT (C) 2026 SOUMYA SHRICHANDANI. ALL RIGHTS RESERVED.
# ==============================================================================

"""
Project J.A.R.V.I.S — Core Application Loop (V3.3 Performance & Anti-Flicker Edition)
Orchestrates: Camera → Tracker → Smoother → Intent → Physics → UI → Display

Enhancements (v3.3):
  [PERF 1] MJPG FourCC & buffer size = 1 for fluid 30-60 FPS with zero lag.
  [PERF 2] Smoothed EMA frame-rate telemetry to stop flickering numbers.
  [PERF 3] Removed destructive failsafe frame-skipping that caused visual strobe.
  [PERF 4] High-efficiency in-place sub-region alpha blending (zero memory copy).
"""

import cv2
import time
import numpy as np
from gesture_v3 import config
from gesture_v3.perception.tracker import HandTracker


class SystemController:
    """
    Main application loop.
    All state is kept here; subsystems are instantiated inside run().
    """

    def __init__(self):
        self.running = True
        
        # Open camera with fallback
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(1)

        # High-performance camera settings: MJPG codec + minimal buffer for zero latency
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, config.TARGET_FPS)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.tracker = HandTracker()
        self.start_time = time.time()
        self.fps = float(config.TARGET_FPS)

        # ---------------------------------------------------------------- #
        # Air-Canvas state
        # ---------------------------------------------------------------- #
        self.draw_mode = False
        self.draw_toggle_start = None
        self.draw_toggle_latched = False
        self.last_draw_toggle_time = 0.0

        # Fist-clear state (must hold for FIST_CLEAR_HOLD_TIME)
        self.fist_clear_start = None
        self.fist_clear_latched = False
        # Stability frame counter — require N consecutive "is_fist" frames
        self.fist_frame_count = 0
        self.FIST_CONFIRM_FRAMES = 8   # ~8 frames of stability

        # ---------------------------------------------------------------- #
        # Radial wheel state
        # ---------------------------------------------------------------- #
        self.radial_trigger_start = None
        self.radial_trigger_latched = False

        # ---------------------------------------------------------------- #
        # Normal-mode state
        # ---------------------------------------------------------------- #
        self.drag_active = False
        self.last_toggle_time = 0.0
        self.last_click_time = 0.0

    # ==================================================================== #
    # Main loop
    # ==================================================================== #

    def run(self):
        print(f"[{config.APP_NAME}] System Initialized | Developed by Soumya Shrichandani. Press 'Q' to Quit.")

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
            # Timing & Anti-Jitter FPS calculation
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

            # ------------------------------------------------------------ #
            # Perception
            # ------------------------------------------------------------ #
            frame_ts_ms = (current_time - self.start_time) * 1000.0
            detection_result = self.tracker.process(img_rgb, frame_ts_ms)

            hand_landmarks = None
            delta_x = delta_y = 0.0
            state = "IDLE"
            confidence = 0.0
            toggle_progress = 0.0

            if detection_result.hand_landmarks:
                hand_landmarks = detection_result.hand_landmarks[0]

                # -------------------------------------------------------- #
                # Air-mouse relative tracking anchor (MCP of index = lm[5])
                # -------------------------------------------------------- #
                raw_point = hand_landmarks[5]
                norm_x, norm_y = raw_point.x, raw_point.y
                filtered_pos = smoother(current_time, [norm_x, norm_y])
                curr_x, curr_y = filtered_pos[0], filtered_pos[1]

                if hasattr(self, 'prev_hand_x'):
                    delta_x = curr_x - self.prev_hand_x
                    delta_y = curr_y - self.prev_hand_y
                self.prev_hand_x = curr_x
                self.prev_hand_y = curr_y

                # -------------------------------------------------------- #
                # Intent classification
                # -------------------------------------------------------- #
                state, meta = classifier.process(hand_landmarks)
                raw_state = state
                confidence = meta.get("confidence", 0.0)
                fingers_up = meta.get("fingers_up", [False] * 5)
                is_toggle_gesture = meta.get("is_toggle", False)
                is_call_sign = meta.get("is_call_sign", False)

                # -------------------------------------------------------- #
                # Coordinate mapping (index fingertip → screen)
                # Linear interpolation with zero clipping or deadzone
                # -------------------------------------------------------- #
                raw_tip = hand_landmarks[8]
                tip_x = float(raw_tip.x)
                tip_y = float(raw_tip.y)

                mx = config.CANVAS_MARGIN_X
                my = config.CANVAS_MARGIN_Y

                clamped_x = max(mx, min(1.0 - mx, tip_x))
                clamped_y = max(my, min(1.0 - my, tip_y))
                raw_screen_x = (clamped_x - mx) / (1.0 - 2 * mx) * config.SCREEN_WIDTH
                raw_screen_y = (clamped_y - my) / (1.0 - 2 * my) * config.SCREEN_HEIGHT

                # Adaptive smoother for anti-tremor + instantaneous response
                screen_x, screen_y = pen_smoother.update(raw_screen_x, raw_screen_y)

                # -------------------------------------------------------- #
                # Rock Sign toggle (DRAW MODE on/off)
                # -------------------------------------------------------- #
                current_time_loop = time.time()

                if is_toggle_gesture:
                    if self.draw_toggle_start is None:
                        self.draw_toggle_start = current_time_loop
                    elapsed = current_time_loop - self.draw_toggle_start
                    toggle_progress = min(1.0, elapsed / config.DRAW_TOGGLE_HOLD_TIME)
                    overlay.update_pill_hold(toggle_progress)

                    if (elapsed >= config.DRAW_TOGGLE_HOLD_TIME
                            and not self.draw_toggle_latched
                            and (current_time_loop - self.last_draw_toggle_time) > config.DRAW_TOGGLE_COOLDOWN):
                        self.draw_mode = not self.draw_mode
                        self.last_draw_toggle_time = current_time_loop
                        self.draw_toggle_latched = True
                        self.draw_toggle_start = None
                        toggle_progress = 0.0
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

                # ======================================================== #
                # AIR CANVAS MODE
                # ======================================================== #
                if self.draw_mode:
                    tool_state = "IDLE"

                    # Priority 0: Exiting via Rock Sign
                    if is_toggle_gesture:
                        overlay.lift_pen()
                        overlay.hide_reticles()
                        overlay.close_radial_wheel()
                        tool_state = "EXITING"

                    # Priority 1: Radial Colour Wheel (Call Sign)
                    elif is_call_sign:
                        overlay.lift_pen()
                        overlay.hide_reticles()

                        if self.radial_trigger_start is None:
                            self.radial_trigger_start = current_time_loop
                        held = current_time_loop - self.radial_trigger_start

                        if (held >= config.RADIAL_TRIGGER_HOLD_TIME and not self.radial_trigger_latched):
                            overlay.open_radial_wheel()
                            self.radial_trigger_latched = True

                        if overlay.radial_active:
                            selected = overlay.update_radial_wheel(screen_x, screen_y)
                            if selected:
                                self.radial_trigger_latched = False
                        tool_state = "COLOR WHEEL"

                    else:
                        self.radial_trigger_start = None
                        self.radial_trigger_latched = False

                        if overlay.radial_active:
                            overlay.close_radial_wheel()

                        # Priority 2: Eraser (3 fingers)
                        if meta.get("is_eraser", False):
                            overlay.erase_at(screen_x, screen_y, radius=config.ERASER_RADIUS)
                            tool_state = "ERASER (3-FINGER)"

                        # Priority 3: Hover (2 fingers / peace)
                        elif meta.get("is_hover", False):
                            overlay.hover_reticle(screen_x, screen_y)
                            tool_state = "HOVER (2-FINGER)"

                        # Priority 4: Draw (1 finger / index only)
                        elif meta.get("is_draw", False):
                            overlay.draw_stroke(screen_x, screen_y)
                            tool_state = "DRAWING (1-FINGER)"

                        # Priority 5: Strict Fist → Clear
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
                                h_img, w_img = img.shape[:2]
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

                    # Camera preview HUD
                    cv2.putText(img, "AIR CANVAS: ACTIVE (DESKTOP OVERLAY)",
                                (20, 70), cv2.FONT_HERSHEY_SIMPLEX,
                                0.65, (255, 255, 0), 2, cv2.LINE_AA)
                    cv2.putText(img, f"TOOL: {tool_state}  |  POS: ({screen_x}, {screen_y})",
                                (20, 98), cv2.FONT_HERSHEY_SIMPLEX,
                                0.50, (200, 255, 255), 1, cv2.LINE_AA)
                    cv2.putText(img, "1-FINGER:Draw  2-FINGER:Hover  3-FINGER:Erase  THUMB+PINKY:Colors  FIST:Clear",
                                (20, 125), cv2.FONT_HERSHEY_PLAIN,
                                0.95, (180, 180, 180), 1, cv2.LINE_AA)

                # ======================================================== #
                # NORMAL MOUSE MODE
                # ======================================================== #
                else:
                    if state == "FIST":
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
                                    (int(norm_x * img.shape[1]),
                                     int(norm_y * img.shape[0])),
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

                    # Draw cinematic HUD in normal mouse mode
                    hud.draw(img, hand_landmarks, state, confidence)

                    # Toggle progress ring
                    if toggle_progress > 0.0:
                        cx_img = img.shape[1] // 2
                        cy_img = img.shape[0] // 2
                        prog_radius = 50
                        angle = int(toggle_progress * 360)
                        cv2.ellipse(img, (cx_img, cy_img),
                                    (prog_radius, prog_radius),
                                    -90, 0, angle, (0, 255, 255), 4, cv2.LINE_AA)
                        cv2.putText(img,
                            f"ENTERING AIR CANVAS: {int(toggle_progress * 100)}%",
                            (cx_img - 150, cy_img + 85),
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
                self.fist_clear_start = None
                self.fist_clear_latched = False
                self.fist_frame_count = 0
                self.radial_trigger_start = None
                self.radial_trigger_latched = False

                if not self.draw_mode:
                    classifier.process(None)
                    hud.draw(img, None, "IDLE", 0.0)

            # ------------------------------------------------------------ #
            # System info overlay & Performance telemetry
            # ------------------------------------------------------------ #
            h_img, w_img = img.shape[:2]

            # Top-left FPS badge with colour coding (Green >= 25, Yellow >= 18, Orange < 18)
            fps_val = int(round(fps))
            fps_color = (0, 255, 0) if fps_val >= 25 else ((0, 255, 255) if fps_val >= 18 else (0, 165, 255))
            cv2.putText(img, f"J.A.R.V.I.S  |  FPS: {fps_val}",
                        (20, 30), cv2.FONT_HERSHEY_PLAIN, 1.2, fps_color, 1, cv2.LINE_AA)

            # High-efficiency in-place watermark band (zero memory copy)
            band_h = 56
            band_y = h_img - band_h
            band_roi = img[band_y:h_img, 0:w_img]
            dark_tint = np.full_like(band_roi, (8, 10, 16))
            cv2.addWeighted(dark_tint, 0.70, band_roi, 0.30, 0, band_roi)

            # Accent line
            cv2.line(img, (0, band_y), (w_img, band_y), (0, 180, 180), 1)

            # Watermark Lines
            cv2.putText(img, "[ SYSTEM ACTIVE ]", (20, band_y + 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(img, "MADE BY - Soumya Shrichandani", (20, band_y + 34),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (220, 220, 220), 1, cv2.LINE_AA)

            label_v3 = "AI WORKSTATION v3.3"
            (tw, _), _ = cv2.getTextSize(label_v3, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
            cv2.putText(img, label_v3, (w_img - tw - 20, band_y + 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 200, 180), 1, cv2.LINE_AA)

            # ------------------------------------------------------------ #
            # Display & UI event pump
            # ------------------------------------------------------------ #
            cv2.imshow(config.APP_NAME, img)

            # Pump Tk overlay event loop
            overlay.update()

            # Key input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                self.running = False
            elif self.draw_mode:
                if key == ord('c') or key == ord('C'):
                    overlay.trigger_scanline_wipe()
                elif key == ord('s') or key == ord('S'):
                    overlay.save_artwork()

        overlay.destroy()
        self.cap.release()
        cv2.destroyAllWindows()
