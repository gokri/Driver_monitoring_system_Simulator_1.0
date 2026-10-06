@echo off
setlocal

set PYTHON=C:\Users\automan\AppData\Local\Programs\Python\Python312\python.exe
cd /d "%~dp0"

echo =====================================================
echo   DEMO 2 -- Driver Monitoring System (LAB PC)
echo   Make sure CARLA 0.9.16 server is running first!
echo =====================================================
echo.

echo Clearing stale state files...
if exist supervisor_state.json del /f supervisor_state.json
if exist _carla_frame.npy del /f _carla_frame.npy

echo Starting Terminal 1 -- setup_demo2.py  (CARLA driving view)
start "Demo2 - Drive" cmd /k "%PYTHON%" setup_demo2.py

timeout /t 3 /nobreak

echo Starting Terminal 2 -- screen_dms.py   (DMS + webcam view)
start "Demo2 - DMS" cmd /k "%PYTHON%" screen_dms.py

echo.
echo Both screens launched.
echo   setup_demo2.py  = driving window (pygame)
echo   screen_dms.py   = DMS + CARLA side-by-side (OpenCV)
echo.
echo Press F in the driving window to toggle fullscreen.
echo Press ESC in any window to close it.
endlocal
