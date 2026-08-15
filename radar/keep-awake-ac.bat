@echo off
cd /d "%~dp0"
echo [Frontier Radar] Prefer: PC stays awake while plugged in
echo.
echo This will set: never sleep / never turn off display while on AC power.
echo (Lid close behavior is unchanged; keep the laptop lid open or set it yourself.)
echo.
pause

powercfg /change standby-timeout-ac 0
powercfg /change monitor-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /change disk-timeout-ac 0

echo.
echo Done for AC power.
echo Also check: Settings - System - Power - Screen and sleep - set to Never when plugged in.
echo.
pause
