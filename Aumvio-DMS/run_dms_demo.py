"""
run_dms_demo.py — DMS on webcam + recorded CARLA video side by side
====================================================================
LEFT  : Webcam → DMS face detection (driver monitoring)
RIGHT : Recorded CARLA video (what the AV sees)

Usage:
    python run_dms_demo.py
    python run_dms_demo.py <path_to_carla_video.mp4>

Press Q to quit, SPACE to pause CARLA video.
"""

import sys
import cv2
import numpy as np
from driver_detection import Face_mesh

CARLA_VIDEO = sys.argv[1] if len(sys.argv) > 1 else (
    r"C:\Users\govin\OneDrive - Nanyang Technological University\Academics\Dissertation"
    r"\WIP\CARLA_SIMULATOR\scripts\recording\recordings"
    r"\session_20260724_142151\clip_0000\video_external.mp4"
)

# ── Open sources ──────────────────────────────────────────────────────────────
webcam = cv2.VideoCapture(0)
if not webcam.isOpened():
    print("ERROR: No webcam found at index 0. Trying index 1...")
    webcam = cv2.VideoCapture(1)

carla  = cv2.VideoCapture(CARLA_VIDEO)
carla_fps = carla.get(cv2.CAP_PROP_FPS) or 5.0
print(f"CARLA video: {CARLA_VIDEO.split(chr(92))[-2]}  {carla_fps:.0f}fps")

print("Loading DMS...")
fm = Face_mesh()
print("DMS ready. Press Q to quit.\n")

paused     = False
frame_idx  = 0
carla_tick = 0

PANEL_W, PANEL_H = 640, 480   # each panel size

def put(img, text, x, y, col=(255,255,255), scale=0.5, thick=1):
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, col, thick)

carla_frame = np.zeros((PANEL_H, PANEL_W, 3), dtype=np.uint8)

while True:
    # ── Webcam frame ──────────────────────────────────────────────────────────
    ret_w, wcam = webcam.read()
    if not ret_w:
        wcam = np.zeros((PANEL_H, PANEL_W, 3), dtype=np.uint8)
        put(wcam, "No webcam signal", 160, 240, col=(0,60,255), scale=1.0)
    else:
        wcam = cv2.resize(wcam, (PANEL_W, PANEL_H))

    # ── CARLA video (advance at carla_fps rate) ───────────────────────────────
    if not paused:
        carla_tick += 1
        # Only advance carla frame every N webcam frames to match its fps
        if carla_tick % max(1, int(30 / carla_fps)) == 0:
            ret_c, cf = carla.read()
            if ret_c:
                carla_frame = cv2.resize(cf, (PANEL_W, PANEL_H))
            else:
                carla.set(cv2.CAP_PROP_POS_FRAMES, 0)   # loop
                frame_idx = 0

    frame_idx += 1

    # ── Run DMS on webcam ─────────────────────────────────────────────────────
    outputs = fm.get_3D_face_mesh(wcam)
    dms_frame = outputs[0] if outputs[0] is not None else wcam.copy()

    # ── Driver state ──────────────────────────────────────────────────────────
    behaviour  = fm.abnormal_behaviour or "—"
    gaze_yaw   = np.mean(fm.gaze_yaw[-5:])  if len(fm.gaze_yaw) > 1  else 0
    head_yaw   = np.mean(fm.angle_yaw[-5:]) if len(fm.angle_yaw) > 1 else 0

    if behaviour == "drowsiness":
        driver_state = "DROWSY";     state_col = (0, 140, 255)
    elif behaviour in ("answering the phone", "texting with phone", "drinking"):
        driver_state = "DISTRACTED"; state_col = (0, 60, 255)
    elif abs(gaze_yaw) > 25 or abs(head_yaw) > 20:
        driver_state = "DISTRACTED"; state_col = (0, 100, 220)
    else:
        driver_state = "ALERT";      state_col = (0, 200, 80)

    # ── DMS panel overlay ─────────────────────────────────────────────────────
    overlay = dms_frame.copy()
    cv2.rectangle(overlay, (0, PANEL_H-90), (PANEL_W, PANEL_H), (0,0,0), -1)
    cv2.addWeighted(overlay, 0.5, dms_frame, 0.5, 0, dms_frame)

    put(dms_frame, f"Behaviour: {behaviour}", 8, PANEL_H-70)
    put(dms_frame, f"Gaze: {gaze_yaw:+.0f}deg  Head: {head_yaw:+.0f}deg", 8, PANEL_H-50)
    put(dms_frame, f"Eye closed: {fm.eye_close}  Yawning: {fm.yawning}", 8, PANEL_H-30)
    put(dms_frame, f"DRIVER: {driver_state}", 8, PANEL_H-8,
        col=state_col, scale=0.65, thick=2)

    # Panel label
    cv2.rectangle(dms_frame, (0,0), (200, 28), (0,0,0), -1)
    put(dms_frame, "DMS — DRIVER CAM", 5, 20, col=(0,200,80), scale=0.55, thick=1)

    # ── CARLA panel overlay ───────────────────────────────────────────────────
    carla_disp = carla_frame.copy()
    cv2.rectangle(carla_disp, (0,0), (240, 28), (0,0,0), -1)
    put(carla_disp, "CARLA — FRONT CAM", 5, 20, col=(255,180,0), scale=0.55)
    put(carla_disp, "PAUSED" if paused else f"Frame {frame_idx}", 5, PANEL_H-10, scale=0.45)

    # ── Supervisor indicator (centre bar) ─────────────────────────────────────
    combined = np.hstack([dms_frame, carla_disp])

    # Top bar showing supervisor status
    bar_h = 36
    bar = np.zeros((bar_h, combined.shape[1], 3), dtype=np.uint8)
    if driver_state == "ALERT":
        cv2.rectangle(bar, (0,0), (combined.shape[1], bar_h), (0,60,0), -1)
        put(bar, "SUPERVISOR: INACTIVE  —  Driver alert", 10, 24,
            col=(0,220,80), scale=0.6, thick=1)
    else:
        cv2.rectangle(bar, (0,0), (combined.shape[1], bar_h), (0,0,100), -1)
        put(bar, f"SUPERVISOR: ACTIVE  —  {driver_state}  —  MPC intervening",
            10, 24, col=(0,100,255), scale=0.6, thick=2)

    display = np.vstack([bar, combined])
    cv2.imshow("DMS + CARLA Demo", display)

    key = cv2.waitKey(33) & 0xFF   # ~30fps
    if key == ord('q'):
        break
    if key == ord(' '):
        paused = not paused
        print(f"{'PAUSED' if paused else 'RESUMED'}")

webcam.release()
carla.release()
cv2.destroyAllWindows()
print("Done.")
