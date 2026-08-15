@echo off
cd /d "%~dp0"
echo Restoring clean radar files from origin/master ...
echo.

where git >nul 2>&1
if errorlevel 1 (
  echo ERROR: git not found.
  pause
  exit /b 1
)

cd /d "%~dp0.."
git fetch origin master
if errorlevel 1 (
  echo ERROR: git fetch failed.
  pause
  exit /b 1
)

git checkout master
git pull origin master
git checkout -- radar/app/pipeline/enrich.py radar/start-worker.bat radar/start-web.bat radar/start-all.bat radar/setup-once.bat radar/check-env.bat radar/stop-all.bat
git restore radar/app/pipeline/enrich.py 2>nul

echo.
echo Done. Your .env was not touched.
echo Now run: radar\start-all.bat
pause
