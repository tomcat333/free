@echo off
cd /d "%~dp0"
echo Stopping Frontier Radar windows/processes ...
taskkill /FI "WINDOWTITLE eq FrontierRadar-Web*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq FrontierRadar-Worker*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq 前沿雷达-网页*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq 前沿雷达-采集*" /T /F >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8787" ^| findstr "LISTENING"') do (
  taskkill /PID %%p /F >nul 2>&1
)
echo Done. If a window is still open, close it manually.
pause
