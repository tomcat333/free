@echo off
cd /d "%~dp0"
set "LINK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\FrontierRadar.lnk"
if exist "%LINK%" (
  del "%LINK%"
  echo Removed auto-start shortcut.
) else (
  echo No auto-start shortcut found.
)
echo.
pause
