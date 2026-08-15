@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo ERROR: missing .venv. Run setup-once.bat first.
  pause
  exit /b 1
)

set "PYTHONPATH=%cd%"
echo [Frontier Radar] Collector worker started.
echo Close this window to stop collecting.
echo.
".venv\Scripts\python.exe" -m app.worker
echo.
echo Collector stopped.
pause
