@echo off
cd /d "%~dp0"

echo [Frontier Radar] First-time setup: create venv and install deps
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: python not found. Install Python 3 and enable "Add python.exe to PATH".
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating .venv ...
  python -m venv .venv
  if errorlevel 1 (
    echo ERROR: failed to create venv.
    pause
    exit /b 1
  )
)

echo Installing requirements ...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo ERROR: pip install failed.
  pause
  exit /b 1
)

echo.
echo Setup done. Next time double-click start-all.bat
pause
