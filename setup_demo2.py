"""
setup_demo2.py — Demo 2: Driver-in-the-Loop (DIL) Simulation
=============================================================
CENTRE SCREEN — Manual driving view with DMS warning overlay

The driver drives manually (keyboard or G29 wheel).
screen_dms.py monitors the driver face via webcam and writes
driver_state (ALERT / DISTRACTED / DROWSY) to supervisor_state.json.
This script reads that state and shows a warning overlay on screen.

Controls:
    W / S        → throttle / brake
    A / D        → steer left / right
    G29 wheel    → auto-detected if connected
    SPACE        → manually force DISTRACTED (demo without webcam)
    R            → manually force DROWSY
    ESC          → quit

Run order:
    Terminal 1: python setup_demo2.py       ← run first (needs CARLA venv)
    Terminal 2: python screen_dms.py        ← webcam + DMS (regular Python)
    Terminal 3: python screen_supervisor.py ← live dashboard
"""

import carla
import pygame
import numpy as np
import math
import time
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, 'supervisor_state.json')

os.environ['SDL_VIDEO_MAXIMIZE_WINDOW'] = '1'   # start maximized
CAM_W, CAM_H = 1920, 1080                       # 1080p for ultrawide fullscreen quality
DEADZONE = 0.05

def pedal_to_01(raw):
    val = (1.0 - raw) / 2.0
    return val if val > DEADZONE else 0.0

def read_driver_state():
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f).get('driver_state', 'ALERT')
    except Exception:
        return 'ALERT'

def write_state(d):
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(d, f)
    except Exception:
        pass

# ── CARLA connect ─────────────────────────────────────────────────────────────
print("\n" + "="*55)
print("  DEMO 2 — Driver-in-the-Loop Simulation")
print("  CARLA 0.9.16  |  Manual Drive + DMS Warning")
print("="*55)

client = carla.Client('localhost', 2000)
client.set_timeout(30.0)
world = client.get_world()
current_map = world.get_map().name
print(f"Using existing map: {current_map}")
# Only reload if not already in a usable town
if 'Town' not in current_map:
    client.set_timeout(120.0)
    world = client.load_world('Town03')
    client.set_timeout(15.0)
print(f"Map: {world.get_map().name}")

world.set_weather(carla.WeatherParameters(
    cloudiness=10.0, precipitation=0.0,
    sun_altitude_angle=65.0, sun_azimuth_angle=160.0,
    fog_density=0.0, wetness=0.0,
))

bp_lib       = world.get_blueprint_library()
spawn_points = world.get_map().get_spawn_points()
tm           = client.get_trafficmanager(8000)
tm.set_global_distance_to_leading_vehicle(5.0)
tm.set_hybrid_physics_mode(True)
tm.global_percentage_speed_difference(20.0)      # 20% slower = calmer, less collision
tm.set_respawn_dormant_vehicles(False)
tm.set_synchronous_mode(False)

settings = world.get_settings()
settings.synchronous_mode = False
world.apply_settings(settings)

# ── Ego vehicle ───────────────────────────────────────────────────────────────
vehicle_bp = bp_lib.find('vehicle.tesla.model3')
vehicle_bp.set_attribute('color', '0,80,255')
vehicle_bp.set_attribute('role_name', 'hero')
ego = None
for sp in spawn_points:
    try:
        ego = world.spawn_actor(vehicle_bp, sp)
        break
    except Exception:
        continue
if ego is None:
    raise RuntimeError("Could not spawn ego vehicle — all spawn points occupied")
print(f"Ego spawned: Tesla Model 3 (blue)")

# ── NPC traffic ───────────────────────────────────────────────────────────────
NPC_COUNT = 8
npc_bps = [bp for bp in bp_lib.filter('vehicle.*')
           if int(bp.get_attribute('number_of_wheels')) == 4]
npcs = []
for sp in spawn_points[1:]:
    if len(npcs) >= NPC_COUNT:
        break
    bp = npc_bps[len(npcs) % len(npc_bps)]
    try:
        npc = world.spawn_actor(bp, sp)
        npc.set_autopilot(True, 8000)
        tm.auto_lane_change(npc, False)          # no lane changes = predictable
        tm.ignore_vehicles_percentage(npc, 0)    # always respect other vehicles
        npcs.append(npc)
    except Exception:
        pass
print(f"Spawned {len(npcs)} NPC vehicles")
print("Settling NPCs for 2s...")
time.sleep(2)                                    # let physics settle before driving

# ── Front camera ──────────────────────────────────────────────────────────────
cam_bp = bp_lib.find('sensor.camera.rgb')
cam_bp.set_attribute('image_size_x', str(CAM_W))
cam_bp.set_attribute('image_size_y', str(CAM_H))
cam_bp.set_attribute('fov', '90')
cam_bp.set_attribute('gamma', '2.2')
camera = world.spawn_actor(
    cam_bp,
    carla.Transform(carla.Location(x=0.3, y=-0.3, z=1.25), carla.Rotation(pitch=-5)),
    attach_to=ego
)
FRAME_FILE = os.path.join(SCRIPT_DIR, '_carla_frame.npy')
latest_image = [None]
def on_image(img):
    arr = np.frombuffer(img.raw_data, dtype=np.uint8)
    frame_bgr = arr.reshape((img.height, img.width, 4))[:, :, :3].copy()   # BGR for OpenCV/DMS
    latest_image[0] = frame_bgr[:, :, ::-1]                                 # RGB for pygame
    try:
        np.save(FRAME_FILE, frame_bgr)
    except Exception:
        pass
camera.listen(on_image)

# ── Joystick (G29 if connected) ───────────────────────────────────────────────
pygame.init()
pygame.joystick.init()
joy = None
if pygame.joystick.get_count() > 0:
    joy = pygame.joystick.Joystick(0)
    joy.init()
    print(f"Steering wheel: {joy.get_name()}")
else:
    print("No wheel — using WASD keyboard")

# Thrustmaster T300RS axis mapping:
#   Axis 0 = steering wheel  (-1=full left, +1=full right)
#   Axis 1 = brake pedal     (middle pedal)
#   Axis 2 = throttle pedal  (right pedal)
#   Axis 3 = clutch pedal    (left pedal) — press to reverse
STEER_AXIS    = 0
BRAKE_AXIS    = 1
THROTTLE_AXIS = 2
CLUTCH_AXIS   = 3
STEER_SCALE   = 0.4   # reduce sensitivity (wheel has large rotation range)
CLUTCH_THRESHOLD = 0.5  # press clutch past 50% to engage reverse

wheel_reverse = [False]

screen = pygame.display.set_mode((CAM_W, CAM_H), pygame.RESIZABLE)
pygame.display.set_caption("Demo 2 — DIL Simulation | Manual Drive")
clock  = pygame.time.Clock()
font_l = pygame.font.SysFont('Consolas', 26, bold=True)
font_m = pygame.font.SysFont('Consolas', 20, bold=True)
font_s = pygame.font.SysFont('Consolas', 14)

# Warning flash state
manual_state = None   # None = use DMS, else 'DISTRACTED' or 'DROWSY'

print("\nDriving. DMS warnings will appear if DISTRACTED or DROWSY detected.")
print("SPACE = force DISTRACTED  |  R = force DROWSY  |  ESC = quit\n")

# ── Main loop ─────────────────────────────────────────────────────────────────
running = True
while running:
    clock.tick(30)

    WIN_W, WIN_H = screen.get_size()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_f:
                pygame.display.toggle_fullscreen()
        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == REVERSE_BTN:
                wheel_reverse[0] = not wheel_reverse[0]
                print(f"Reverse: {'ON' if wheel_reverse[0] else 'OFF'}")

    # ── Driver state ──────────────────────────────────────────────────────────
    driver_state = manual_state if manual_state else read_driver_state()

    # ── Driver input ──────────────────────────────────────────────────────────
    keys = pygame.key.get_pressed()
    if joy:
        raw_steer = joy.get_axis(STEER_AXIS)
        steer     = max(-1.0, min(1.0, raw_steer * STEER_SCALE))
        throttle  = pedal_to_01(joy.get_axis(THROTTLE_AXIS))
        brake     = pedal_to_01(joy.get_axis(BRAKE_AXIS))
        clutch    = pedal_to_01(joy.get_axis(CLUTCH_AXIS))
        reverse   = clutch > CLUTCH_THRESHOLD
    else:
        reverse  = keys[pygame.K_q]
        throttle = 0.5 if (keys[pygame.K_w] or reverse) else 0.0
        brake    = 0.8 if keys[pygame.K_s] else 0.0
        steer    = (-0.4 if keys[pygame.K_a] else
                     0.4 if keys[pygame.K_d] else 0.0)

    ego.apply_control(carla.VehicleControl(
        throttle=float(throttle),
        brake=float(brake),
        steer=float(steer),
        reverse=bool(reverse),
    ))

    # Write state for supervisor dashboard
    v = ego.get_velocity()
    speed = math.sqrt(v.x**2 + v.y**2 + v.z**2) * 3.6
    write_state({
        "driver_state": driver_state,
        "ego_speed_kmh": round(speed, 1),
    })

    # ── Render ────────────────────────────────────────────────────────────────
    if latest_image[0] is not None:
        surf = pygame.surfarray.make_surface(
            np.transpose(latest_image[0], (1, 0, 2)))
        surf = pygame.transform.scale(surf, (WIN_W, WIN_H))
        screen.blit(surf, (0, 0))
    else:
        screen.fill((20, 20, 30))

    # Bottom info bar
    bar = pygame.Surface((WIN_W, 36), pygame.SRCALPHA)
    bar.fill((0, 0, 0, 160))
    screen.blit(bar, (0, WIN_H - 36))
    input_mode = f"Wheel: {joy.get_name()[:20]}" if joy else "Keyboard: WASD"
    rev_str    = "  [REV]" if reverse else ""
    screen.blit(font_s.render(
        f"Demo 2  -  DIL  |  {speed:.1f} km/h{rev_str}  |  {input_mode}  |  ESC=quit",
        True, (120, 150, 180)), (10, WIN_H - 26))

    # Corner state chip only — no banner, no flash
    sc = {
        "ALERT":         (60,  220, 100),
        "DISTRACTED":    (255, 140,   0),
        "DROWSY":        (255,  50,  50),
        "DRIVER ABSENT": (160, 160, 160),
    }.get(driver_state, (200, 200, 200))
    chip = pygame.Surface((260, 36), pygame.SRCALPHA)
    chip.fill((*sc, 210))
    screen.blit(chip, (10, 10))
    screen.blit(font_m.render(f"  {driver_state}", True, (10, 10, 10)), (10, 14))

    pygame.display.flip()

# ── Cleanup ───────────────────────────────────────────────────────────────────
camera.stop(); camera.destroy()
for npc in npcs:
    try: npc.destroy()
    except Exception: pass
ego.destroy()
pygame.quit()
print("Demo 2 closed.")
