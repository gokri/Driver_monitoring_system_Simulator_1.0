@echo off
setlocal

set PYTHON=C:\Users\automan\AppData\Local\Programs\Python\Python312\python.exe
cd /d "%~dp0"

echo =====================================================
echo   DEMO 2 -- Driver Monitoring System (LAB PC)
echo   Make sure CARLA 0.9.16 server is running first!
echo =====================================================
echo.

echo Starting Terminal 1 -- screen_dms.py   (DMS loading CLIP ~15s)
start "Demo2 - DMS" cmd /k "%PYTHON%" screen_dms.py

timeout /t 12 /nobreak

echo Starting Terminal 2 -- setup_demo2.py  (CARLA driving view)
start "Demo2 - Drive" cmd /k "%PYTHON%" setup_demo2.py

echo.
echo Both screens launched.
echo   setup_demo2.py  = driving window (pygame)
echo   screen_dms.py   = DMS + CARLA side-by-side (OpenCV)
echo.
echo Press F in the driving window to toggle fullscreen.
echo Press ESC in any window to close it.
endlocal
