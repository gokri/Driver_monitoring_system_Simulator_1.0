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
import threading

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
cap = None
for idx in ([CAM_IDX] + [i for i in range(3) if i != CAM_IDX]):
    c = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
    if c.isOpened():
        ret, test = c.read()
        if ret and test is not None:
            cap = c
            print(f"  Webcam opened on index {idx}")
            break
        c.release()
if cap is None:
    print("  WARNING: No webcam found — showing blank panel")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_FPS, 30)

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

# ── Shared DMS result (updated by background thread) ─────────────────────────
_lock        = threading.Lock()
_dms_result  = {
    "dms_frame":   None,
    "face_found":  False,
    "behaviour":   "—",
    "gaze_yaw":    0.0,
    "head_yaw":    0.0,
    "pitch":       0.0,
    "driver_state": "ALERT",
    "state_col":   (0, 200, 80),
}
_stop_thread  = threading.Event()
_eye_close_since = [None]   # timestamp when eyes first closed
EYE_CLOSE_THRESHOLD = 1.5   # seconds eyes must stay closed to trigger DROWSY

def dms_worker():
    while not _stop_thread.is_set():
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.03)
            continue
        # Flush webcam buffer — grab latest frame, discard stale ones
        for _ in range(2):
            cap.grab()
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.resize(frame, (PANEL_W, PANEL_H))
        outputs   = fm.get_3D_face_mesh(frame)
        dms_frame = outputs[0] if outputs[0] is not None else frame.copy()
        face_found = outputs[0] is not None
        behaviour = fm.abnormal_behaviour or "—"
        gaze_yaw  = float(np.mean(fm.gaze_yaw[-5:]))   if len(fm.gaze_yaw)   > 1 else 0.0
        head_yaw  = float(np.mean(fm.angle_yaw[-5:]))   if len(fm.angle_yaw)  > 1 else 0.0
        pitch     = float(np.mean(fm.angle_pitch[-5:])) if len(fm.angle_pitch) > 1 else 0.0
        # Eye close timer — ignore blinks, only trigger after 1.5s
        if fm.eye_close:
            if _eye_close_since[0] is None:
                _eye_close_since[0] = time.time()
            sustained_eye_close = (time.time() - _eye_close_since[0]) >= EYE_CLOSE_THRESHOLD
        else:
            _eye_close_since[0] = None
            sustained_eye_close = False

        if not face_found:
            state, col = "DRIVER ABSENT", (160, 160, 160)
        elif behaviour == "drowsiness" or sustained_eye_close:
            state, col = "DROWSY", (0, 140, 255)
        elif behaviour in ("answering the phone", "texting with phone", "drinking"):
            state, col = "DISTRACTED", (0, 60, 255)
        elif abs(gaze_yaw) > 25 or abs(head_yaw) > 20:
            state, col = "DISTRACTED", (0, 100, 220)
        else:
            state, col = "ALERT", (0, 200, 80)
        write_dms_state(state, {
            "dms_behaviour": behaviour,
            "dms_gaze_yaw":  round(gaze_yaw, 1),
            "dms_head_yaw":  round(head_yaw, 1),
            "dms_pitch":     round(pitch, 1),
        })
        with _lock:
            _dms_result.update({
                "dms_frame": dms_frame, "face_found": face_found,
                "behaviour": behaviour, "gaze_yaw": gaze_yaw,
                "head_yaw": head_yaw,   "pitch": pitch,
                "driver_state": state,  "state_col": col,
            })

t_dms = threading.Thread(target=dms_worker, daemon=True)
t_dms.start()

driver_state = "ALERT"
frame_count  = 0
t0           = time.time()

WIN_NAME = "Demo 2 - DMS + CARLA Live"
cv2.namedWindow(WIN_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WIN_NAME, PANEL_W * 2, PANEL_H + 36)
cv2.moveWindow(WIN_NAME, 100, 100)

print(f"Running. Writing state to {STATE_FILE}")
print("Press Q or ESC to quit.\n")

while True:
    # ── Read latest DMS result from thread ────────────────────────────────────
    with _lock:
        r          = dict(_dms_result)
    dms_frame    = r["dms_frame"]
    face_found   = r["face_found"]
    behaviour    = r["behaviour"]
    gaze_yaw     = r["gaze_yaw"]
    head_yaw     = r["head_yaw"]
    pitch        = r["pitch"]
    driver_state = r["driver_state"]
    state_col    = r["state_col"]

    # If DMS thread hasn't produced a frame yet, show placeholder
    if dms_frame is None:
        dms_frame = np.zeros((PANEL_H, PANEL_W, 3), dtype=np.uint8)
        put(dms_frame, "Starting DMS...", 160, 240, col=(100, 100, 100), scale=0.8)

    # Show "NO FACE" banner when driver is out of frame
    if not face_found:
        cv2.rectangle(dms_frame, (0, PANEL_H//2 - 30), (PANEL_W, PANEL_H//2 + 30), (40, 40, 40), -1)
        put(dms_frame, "NO FACE DETECTED", PANEL_W//2 - 110, PANEL_H//2 + 8,
            col=(160, 160, 160), scale=0.8, thick=2)

    # ── Live CARLA frame ──────────────────────────────────────────────────────
    try:
        raw = np.load(FRAME_FILE)
        carla_frame = cv2.resize(raw, (PANEL_W, PANEL_H))
    except Exception:
        pass

    frame_count += 1

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
    if len(dms_frame.shape) == 2:
        dms_frame = cv2.cvtColor(dms_frame, cv2.COLOR_GRAY2BGR)
    if len(carla_disp.shape) == 2:
        carla_disp = cv2.cvtColor(carla_disp, cv2.COLOR_GRAY2BGR)
    combined = np.hstack([dms_frame, carla_disp])
    display = combined
    cv2.imshow(WIN_NAME, display)

    key = cv2.waitKey(1) & 0xFF
    if key in (ord('q'), ord('Q'), 27):
        break

_stop_thread.set()
cap.release()
cv2.destroyAllWindows()
print("DMS screen closed.")
