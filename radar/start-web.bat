@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo ERROR: missing .venv. Run setup-once.bat first.
  pause
  exit /b 1
)

set "PYTHONPATH=%cd%"
set "PORT=8787"
echo [Frontier Radar] Web UI: http://127.0.0.1:%PORT%
if exist ".env" (
  echo [config] found .env
) else if exist ".env.txt" (
  echo [warn] found .env.txt - rename it to .env
) else (
  echo [warn] no .env in this folder - LLM intro will be disabled
)
echo Close this window to stop the web server.
echo.
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port %PORT%
echo.
echo Web server stopped.
pause
