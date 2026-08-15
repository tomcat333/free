@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo ERROR: missing .venv. Run setup-once.bat first.
  pause
  exit /b 1
)

echo [Frontier Radar] Starting web + collector ...
start "FrontierRadar-Web" "%~dp0start-web.bat"
timeout /t 2 /nobreak >nul
start "FrontierRadar-Worker" "%~dp0start-worker.bat"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8787"

echo.
echo Opened two console windows and the browser.
echo UI: http://127.0.0.1:8787
echo To stop: close those two windows, or run stop-all.bat
echo.
pause
