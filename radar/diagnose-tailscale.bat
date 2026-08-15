@echo off
cd /d "%~dp0"
echo [Frontier Radar] Diagnose remote access
echo.

echo === 1) Is web listening on all interfaces? ===
netstat -ano | findstr ":8787" | findstr "LISTENING"
echo.
echo Expect a line with 0.0.0.0:8787
echo If you only see 127.0.0.1:8787, restart with latest start-all.bat
echo.

echo === 2) Firewall rule ===
netsh advfirewall firewall show rule name="Frontier Radar 8787"
echo.

echo === 3) Tailscale on THIS PC ===
where tailscale >nul 2>&1
if errorlevel 1 (
  echo Tailscale CLI not in PATH. Check tray icon instead.
) else (
  tailscale status
  echo.
  echo This PC Tailscale IPv4:
  tailscale ip -4
)
echo.

echo === 4) About 100.64 vs 100.112 ===
echo Both are normal Tailscale addresses ^(range 100.64.0.0 - 100.127.x.x^).
echo Different prefixes alone do NOT block access.
echo.

echo === 5) What to do on Surface ===
echo A. Same Tailscale account, status Connected
echo B. On Surface PowerShell:  ping -n 4 ^<HOME-PC-100.x.y.z^>
echo    - ping fails  = Tailscale/account/network problem ^(not radar^)
echo    - ping works  = then open http://^<HOME-PC-IP^>:8787 in browser
echo C. Do NOT use 127.0.0.1 on Surface
echo.

echo === 6) Extra firewall allow for python.exe ===
if exist ".venv\Scripts\python.exe" (
  echo Will also allow .venv python.exe inbound ^(Admin prompt may appear^).
) else (
  echo No .venv python yet.
)
echo.
pause

net session >nul 2>&1
if errorlevel 1 (
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

netsh advfirewall firewall delete rule name="Frontier Radar 8787" >nul 2>&1
netsh advfirewall firewall add rule name="Frontier Radar 8787" dir=in action=allow protocol=TCP localport=8787 profile=any >nul

if exist ".venv\Scripts\python.exe" (
  netsh advfirewall firewall delete rule name="Frontier Radar Python" >nul 2>&1
  netsh advfirewall firewall add rule name="Frontier Radar Python" dir=in action=allow program="%~dp0.venv\Scripts\python.exe" enable=yes profile=any
  echo Allowed program: %~dp0.venv\Scripts\python.exe
)

echo.
echo Done. Restart start-all.bat, then on Surface:
echo   1) ping HOME-PC Tailscale IP
echo   2) open http://HOME-PC-IP:8787
echo.
pause
