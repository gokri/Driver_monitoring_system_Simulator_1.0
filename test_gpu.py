"""
test_gpu.py — GPU / CUDA diagnostic (safe to run anytime, changes nothing)
Run: python test_gpu.py
"""

import sys
print(f"Python: {sys.version}\n")

# ── 1. Torch ──────────────────────────────────────────────────────────────────
try:
    import torch
    print(f"torch version   : {torch.__version__}")
    print(f"CUDA available  : {torch.cuda.is_available()}")
    print(f"CUDA version    : {torch.version.cuda}")
    print(f"cuDNN version   : {torch.backends.cudnn.version()}")

    if torch.cuda.is_available():
        print(f"GPU name        : {torch.cuda.get_device_name(0)}")
        print(f"GPU memory      : {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        # Quick tensor test
        x = torch.tensor([1.0]).cuda()
        print(f"Tensor on GPU   : {x.device}  ✓")
    else:
        print("\n[!] CUDA not available — checking why...\n")

        # Check if it's a CPU-only torch build
        if '+cpu' in torch.__version__:
            print("  CAUSE: CPU-only torch is installed (+cpu build)")
            print("  FIX  : pip install torch --index-url https://download.pytorch.org/whl/cu128")
        else:
            print("  torch build looks GPU-capable — CUDA runtime may be blocked")
            print("  Try running the DLL check below")

except ImportError:
    print("torch not installed")
except Exception as e:
    print(f"torch error: {e}")

print()

# ── 2. Check CUDA DLL accessibility ──────────────────────────────────────────
import ctypes, os

cuda_dlls = [
    "nvcuda.dll",
    "cudart64_12.dll",
    "cublas64_12.dll",
    "cudnn64_9.dll",
]

print("CUDA DLL check:")
for dll in cuda_dlls:
    try:
        lib = ctypes.CDLL(dll)
        print(f"  {dll:30s} OK")
    except OSError as e:
        print(f"  {dll:30s} FAILED — {e}")

print()

# ── 3. NVIDIA driver ─────────────────────────────────────────────────────────
print("NVIDIA driver check:")
try:
    import subprocess
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,cuda_version",
         "--format=csv,noheader"],
        capture_output=True, text=True, timeout=5
    )
    if result.returncode == 0:
        print(f"  {result.stdout.strip()}")
    else:
        print(f"  nvidia-smi failed: {result.stderr.strip()}")
except FileNotFoundError:
    print("  nvidia-smi not found in PATH")
except Exception as e:
    print(f"  {e}")

print()

# ── 4. Installed torch packages ───────────────────────────────────────────────
print("Installed torch packages:")
try:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list"],
        capture_output=True, text=True
    )
    for line in result.stdout.splitlines():
        if any(k in line.lower() for k in ["torch", "cuda", "nvidia"]):
            print(f"  {line}")
except Exception as e:
    print(f"  {e}")
