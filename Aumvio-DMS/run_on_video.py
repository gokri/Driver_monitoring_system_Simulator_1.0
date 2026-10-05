"""
run_on_video.py — Run Aumovio DMS on a recorded video file
============================================================
Usage:
    python run_on_video.py <path_to_video.mp4>

Example:
    python run_on_video.py "C:/Users/govin/.../clip_0000/video_external.mp4"

Shows DMS analysis frame-by-frame on a recorded video.
Press Q to quit, SPACE to pause.
"""

import sys
import cv2
import time
import numpy as np
from driver_detection import Face_mesh

VIDEO_PATH = sys.argv[1] if len(sys.argv) > 1 else (
    r"C:\Users\govin\OneDrive - Nanyang Technological University\Academics\Dissertation"
    r"\WIP\CARLA_SIMULATOR\scripts\recording\recordings"
    r"\session_20260724_142151\clip_0000\video_external.mp4"
)

print(f"Loading video: {VIDEO_PATH}")
cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("ERROR: Cannot open video file.")
    sys.exit(1)

fps    = cap.get(cv2.CAP_PROP_FPS) or 30
total  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
w      = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h      = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Video: {w}x{h}  {fps:.1f}fps  {total} frames  ({total/fps:.1f}s)")

print("Loading DMS (CLIP model download on first run ~350MB)...")
fm = Face_mesh()
print("DMS ready.\n")

paused    = False
frame_idx = 0

while cap.isOpened():
    if not paused:
        ret, frame = cap.read()
        if not ret:
            print("End of video.")
            break
        frame_idx += 1

    # Run DMS
    outputs = fm.get_3D_face_mesh(frame)
    annotated_frame = outputs[0]   # face landmarks overlay
    face_mesh_img   = outputs[1]   # head pose axes
    left_eye_img    = outputs[2]
    right_eye_img   = outputs[3]
    mouth_img       = outputs[4]

    # ── Build display ──────────────────────────────────────────────────────────
    disp = annotated_frame.copy()

    # State overlay
    behaviour  = fm.abnormal_behaviour if fm.abnormal_behaviour else "—"
    expression = fm.expression        if fm.expression        else "—"
    gaze_yaw   = np.mean(fm.gaze_yaw[-5:])   if fm.gaze_yaw   else 0
    head_yaw   = np.mean(fm.angle_yaw[-5:])  if fm.angle_yaw  else 0

    # Driver state logic (mirrors CARLA supervisor)
    if behaviour in ("drowsiness",):
        driver_state = "DROWSY"
        state_col    = (0, 140, 255)
    elif behaviour in ("answering the phone", "texting with phone", "drinking"):
        driver_state = "DISTRACTED"
        state_col    = (0, 60, 255)
    elif abs(gaze_yaw) > 25 or abs(head_yaw) > 20:
        driver_state = "DISTRACTED (gaze)"
        state_col    = (0, 100, 220)
    else:
        driver_state = "ALERT"
        state_col    = (0, 200, 80)

    # HUD
    overlay = disp.copy()
    cv2.rectangle(overlay, (0, 0), (disp.shape[1], 110), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, disp, 0.45, 0, disp)

    def put(img, text, x, y, col=(255,255,255), scale=0.55, thick=1):
        cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, col, thick)

    put(disp, f"Frame: {frame_idx}/{total}  ({frame_idx/fps:.1f}s)", 10, 22)
    put(disp, f"Behaviour : {behaviour}  ({fm.behaviour_score:.0f}%)", 10, 46)
    put(disp, f"Expression: {expression}", 10, 68)
    put(disp, f"Gaze yaw: {gaze_yaw:+.1f}deg   Head yaw: {head_yaw:+.1f}deg", 10, 90)
    put(disp, f"DRIVER STATE: {driver_state}", 10, 115, col=state_col, scale=0.7, thick=2)

    if fm.eye_close:
        put(disp, "EYE CLOSED", disp.shape[1]-160, 30, col=(0,60,255), scale=0.6, thick=2)
    if fm.yawning:
        put(disp, "YAWNING",    disp.shape[1]-140, 55, col=(0,140,255), scale=0.6, thick=2)

    # Face mesh panel (right side)
    if face_mesh_img is not None and face_mesh_img.shape[0] > 10:
        panel = cv2.resize(face_mesh_img, (200, 200))
        disp[10:210, disp.shape[1]-210:disp.shape[1]-10] = panel

    cv2.imshow("DMS Analysis — " + VIDEO_PATH.split("\\")[-2], disp)

    key = cv2.waitKey(max(1, int(1000/fps))) & 0xFF
    if key == ord('q'):
        break
    if key == ord(' '):
        paused = not paused
        print(f"{'PAUSED' if paused else 'RESUMED'} at frame {frame_idx}")

cap.release()
cv2.destroyAllWindows()
print(f"\nProcessed {frame_idx} frames.")
print(f"Final driver state: {driver_state}")
