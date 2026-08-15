@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo 还没有安装依赖。请先双击 setup-once.bat
  pause
  exit /b 1
)

echo [前沿雷达] 正在打开网页服务 + 采集进程 ...
start "前沿雷达-网页" "%~dp0start-web.bat"
timeout /t 2 /nobreak >nul
start "前沿雷达-采集" "%~dp0start-worker.bat"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8787"

echo.
echo 已启动两个黑窗口，并尝试打开浏览器。
echo - 看简报：http://127.0.0.1:8787
echo - 想停止：分别关掉那两个黑窗口即可
echo.
pause
