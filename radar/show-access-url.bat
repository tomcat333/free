@echo off
cd /d "%~dp0"
echo [Frontier Radar] Access URLs
echo.

echo Local on this PC:
echo   http://127.0.0.1:8787
echo.

where tailscale >nul 2>&1
if errorlevel 1 (
  echo Tailscale CLI not found in PATH.
  echo Open Tailscale tray icon to see the 100.x.y.z IP, then on other devices open:
  echo   http://100.x.y.z:8787
) else (
  for /f "delims=" %%i in ('tailscale ip -4 2^>nul') do set "TSIP=%%i"
  if defined TSIP (
    echo Tailscale IP of THIS computer:
    echo   %TSIP%
    echo.
    echo On phone / Surface / office PC ^(same Tailscale account^), open:
    echo   http://%TSIP%:8787
  ) else (
    echo Could not read Tailscale IP. Is Tailscale Connected?
  )
)

echo.
echo Checklist if another device cannot connect:
echo   1. Home PC: start-all.bat is running
echo   2. Other device: Tailscale Connected, SAME account as home PC
echo   3. Home PC: run allow-firewall-8787.bat once ^(Admin^)
echo   4. Use the home PC Tailscale IP, not 127.0.0.1, on the other device
echo.
pause
