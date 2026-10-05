# Driver Monitoring System Simulator — Demo 2

> **PRIVATE REPOSITORY **  
> Contains Aumovio DMS engine used with permission for academic research (NTU Dissertation).  
> Not for redistribution.

Driver-in-the-Loop (DIL) simulation combining manual driving in CARLA with real-time  
driver state monitoring via the Aumovio DMS engine (MediaPipe + CLIP).

## What it shows

| Screen | File | Description |
|---|---|---|
| Centre — Driving view | `setup_demo2.py` | Manual driving in CARLA + driver state chip |
| Side-by-side — DMS | `screen_dms.py` | Webcam face detection + live CARLA feed |

## Driver states detected

| State | Trigger |
|---|---|
| ALERT | Eyes on road, no abnormal behaviour |
| DISTRACTED | Gaze yaw > 25° or head yaw > 20°, or phone/drinking/texting detected |
| DROWSY | Eyes closed (PERCLOS), yawning, or drowsiness classified by CLIP |
| DRIVER ABSENT | No face detected in webcam frame |

## DMS Engine

Located in `Aumvio-DMS/` 
Source: https://github.com/EzhangHZ/Aumvio-DMS-demo (private)  
Uses MediaPipe Face Mesh for head pose + iris tracking, and CLIP ViT-B/16 for behaviour classification.

## Requirements

- CARLA 0.9.16 server running
- Python 3.12 with `carla==0.9.16` wheel (for `setup_demo2.py`)
- Regular Python 3.12 (for `screen_dms.py`)

```
# carla_0916 venv (for setup_demo2.py)
pip install pygame numpy carla==0.9.16

# regular Python (for screen_dms.py)
pip install mediapipe==0.10.13 opencv-python torch clip-by-openai Pillow PyQt5
```

## How to run

Start CARLA 0.9.16 server first, then open **2 terminals** in this folder.

**Terminal 1** — CARLA venv interpreter:
```bash
carla_0916\Scripts\python.exe setup_demo2.py
```
Wait for `Ego spawned` before starting Terminal 2.

**Terminal 2** — regular Python:
```bash
python screen_dms.py
```

## Controls (driving window)

| Key | Action |
|---|---|
| `W` | Throttle |
| `S` | Brake |
| `A` / `D` | Steer left / right |
| `Q` | Reverse |
| `ESC` | Quit |

## Notes

- `screen_dms.py` uses camera index 0 by default. Pass `1` as argument if webcam is on index 1: `python screen_dms.py 1`
- The CARLA frame is shared via `_carla_frame.npy` (auto-created, safe to delete after run)
- `supervisor_state.json` holds live driver state shared between both scripts
