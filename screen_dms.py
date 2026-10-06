"""
screen_dms.py — Demo 2: DMS Screen
====================================
LEFT  : Webcam → Aumovio DMS face detection (exact original logic)
RIGHT : Live CARLA driving view (from setup_demo2.py)

DMS logic is identical to run_dms_demo.py:
  behaviour == "drowsiness"              → DROWSY
  behaviour in (phone/text/drink)        → DISTRACTED
  abs(gaze_yaw) > 25 or abs(head_yaw) > 20 → DISTRACTED
  no face detected                       → DRIVER ABSENT
  otherwise                              → ALERT

Writes driver_state to supervisor_state.json for setup_demo2.py to read.

Usage:
    python screen_dms.py
    python screen_dms.py 1    (camera index 1)

Press Q or ESC to quit.
"""

import cv2
import numpy as np
import json
import os
import sys
import time

DEMO2_DIR  = os.path.dirname(os.path.abspath(__file__))
DMS_DIR    = os.path.join(DEMO2_DIR, 'Aumvio-DMS')
STATE_FILE = os.path.join(DEMO2_DIR, 'supervisor_state.json')
FRAME_FILE = os.path.join(DEMO2_DIR, '_carla_frame.npy')

sys.path.insert(0, DMS_DIR)
os.chdir(DMS_DIR)

CAM_IDX    = int(sys.argv[1]) if len(sys.argv) > 1 else 0
PANEL_W, PANEL_H = 640, 480

# ── Load DMS ──────────────────────────────────────────────────────────────────
print("Loading Aumovio DMS (CLIP ViT-B/16 + MediaPipe)...")
print("  ~15s on first run...")
from driver_detection import Face_mesh
fm = Face_mesh()
print("  DMS ready.\n")

# ── Camera ────────────────────────────────────────────────────────────────────
cap = cv2.VideoCapture(CAM_IDX)
if not cap.isOpened():
    cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# ── State writer ──────────────────────────────────────────────────────────────
def write_dms_state(driver_state, extras={}):
    try:
        try:
            with open(STATE_FILE, 'r') as f:
                d = json.load(f)
        except Exception:
            d = {}
        d['driver_state'] = driver_state
        d.update(extras)
        with open(STATE_FILE, 'w') as f:
            json.dump(d, f)
    except Exception:
        pass

def put(img, text, x, y, col=(255, 255, 255), scale=0.5, thick=1):
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, col, thick)

carla_frame = np.zeros((PANEL_H, PANEL_W, 3), dtype=np.uint8)
put(carla_frame, "Waiting for CARLA...", 160, 240, col=(100, 100, 100), scale=0.8)

driver_state = "ALERT"
frame_count  = 0
t0           = time.time()

WIN_NAME = "Demo 2 - DMS + CARLA Live"
cv2.namedWindow(WIN_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WIN_NAME, PANEL_W * 2, PANEL_H + 36)

print(f"Running. Writing state to {STATE_FILE}")
print("Press Q or ESC to quit.\n")

while True:
    ret, wcam = cap.read()
    if not ret:
        wcam = np.zeros((PANEL_H, PANEL_W, 3), dtype=np.uint8)
        put(wcam, "No webcam signal", 160, 240, col=(0, 60, 255), scale=1.0)
    else:
        wcam = cv2.resize(wcam, (PANEL_W, PANEL_H))

    # ── Live CARLA frame ──────────────────────────────────────────────────────
    try:
        raw = np.load(FRAME_FILE)
        carla_frame = cv2.resize(raw, (PANEL_W, PANEL_H))
    except Exception:
        pass   # keep last good frame

    frame_count += 1

    # ── Run Aumovio DMS — exact original logic ────────────────────────────────
    outputs    = fm.get_3D_face_mesh(wcam)
    dms_frame  = outputs[0] if outputs[0] is not None else wcam.copy()
    face_found = outputs[0] is not None

    behaviour = fm.abnormal_behaviour or "—"
    gaze_yaw  = float(np.mean(fm.gaze_yaw[-5:]))  if len(fm.gaze_yaw)  > 1 else 0.0
    head_yaw  = float(np.mean(fm.angle_yaw[-5:]))  if len(fm.angle_yaw)  > 1 else 0.0
    pitch     = float(np.mean(fm.angle_pitch[-5:])) if len(fm.angle_pitch) > 1 else 0.0

    # ── Exact Aumovio state logic (from run_dms_demo.py) ─────────────────────
    if not face_found:
        driver_state = "DRIVER ABSENT"
        state_col    = (160, 160, 160)
    elif behaviour == "drowsiness" or fm.eye_close:
        driver_state = "DROWSY"
        state_col    = (0, 140, 255)
    elif behaviour in ("answering the phone", "texting with phone", "drinking"):
        driver_state = "DISTRACTED"
        state_col    = (0, 60, 255)
    elif abs(gaze_yaw) > 25 or abs(head_yaw) > 20:
        driver_state = "DISTRACTED"
        state_col    = (0, 100, 220)
    else:
        driver_state = "ALERT"
        state_col    = (0, 200, 80)

    write_dms_state(driver_state, {
        "dms_behaviour": behaviour,
        "dms_gaze_yaw":  round(gaze_yaw, 1),
        "dms_head_yaw":  round(head_yaw, 1),
        "dms_pitch":     round(pitch, 1),
        "dms_fps":       round(frame_count / max(time.time() - t0, 0.001), 1),
    })

    # ── DMS panel overlay ─────────────────────────────────────────────────────
    overlay = dms_frame.copy()
    cv2.rectangle(overlay, (0, PANEL_H - 90), (PANEL_W, PANEL_H), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, dms_frame, 0.5, 0, dms_frame)

    put(dms_frame, f"Behaviour: {behaviour}",                       8, PANEL_H - 70)
    put(dms_frame, f"Gaze: {gaze_yaw:+.0f}deg  Head: {head_yaw:+.0f}deg", 8, PANEL_H - 50)
    put(dms_frame, f"Eye closed: {fm.eye_close}  Yawning: {fm.yawning}", 8, PANEL_H - 30)
    put(dms_frame, f"DRIVER: {driver_state}",                       8, PANEL_H - 8,
        col=state_col, scale=0.65, thick=2)

    cv2.rectangle(dms_frame, (0, 0), (220, 28), (0, 0, 0), -1)
    put(dms_frame, "DMS - DRIVER CAM", 5, 20, col=(0, 200, 80), scale=0.55)

    # ── CARLA panel overlay ───────────────────────────────────────────────────
    carla_disp = carla_frame.copy()
    cv2.rectangle(carla_disp, (0, 0), (260, 28), (0, 0, 0), -1)
    put(carla_disp, "CARLA - DRIVER VIEW", 5, 20, col=(255, 180, 0), scale=0.55)

    dms_frame  = cv2.resize(dms_frame,  (PANEL_W, PANEL_H))
    carla_disp = cv2.resize(carla_disp, (PANEL_W, PANEL_H))
    combined = np.hstack([dms_frame, carla_disp])
    display = combined
    cv2.imshow(WIN_NAME, display)

    key = cv2.waitKey(1) & 0xFF
    if key in (ord('q'), ord('Q'), 27):
        break

cap.release()
cv2.destroyAllWindows()
print("DMS screen closed.")
