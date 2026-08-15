@echo off
cd /d "%~dp0"
echo [Frontier Radar] Allow TCP 8787 in Windows Firewall
echo This lets phone / Surface / office PC reach the service via Tailscale.
echo.
echo You may see a UAC prompt - choose Yes.
echo.
pause

net session >nul 2>&1
if errorlevel 1 (
  echo Requesting Administrator...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

netsh advfirewall firewall delete rule name="Frontier Radar 8787" >nul 2>&1
netsh advfirewall firewall add rule name="Frontier Radar 8787" dir=in action=allow protocol=TCP localport=8787 profile=any

if exist "%~dp0.venv\Scripts\python.exe" (
  netsh advfirewall firewall delete rule name="Frontier Radar Python" >nul 2>&1
  netsh advfirewall firewall add rule name="Frontier Radar Python" dir=in action=allow program="%~dp0.venv\Scripts\python.exe" enable=yes profile=any
  echo Also allowed: .venv\Scripts\python.exe
)

if errorlevel 1 (
  echo ERROR: failed to add firewall rule.
) else (
  echo OK: inbound TCP 8787 allowed.
  echo Restart start-all.bat on the home PC if it is already running.
)

echo.
pause
