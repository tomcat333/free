@echo off
cd /d "%~dp0"
echo [Frontier Radar] Install auto-start on Windows logon
echo.

set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "LINK=%STARTUP%\FrontierRadar.lnk"
set "TARGET=%~dp0start-all.bat"

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%LINK%'); $s.TargetPath = '%TARGET%'; $s.WorkingDirectory = '%~dp0'; $s.WindowStyle = 7; $s.Save()"

if exist "%LINK%" (
  echo OK: shortcut created:
  echo   %LINK%
  echo.
  echo After you log into Windows, start-all.bat will run automatically.
  echo To remove auto-start later, delete that shortcut or run remove-autostart.bat
) else (
  echo ERROR: failed to create startup shortcut.
)

echo.
pause
