@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo 还没有安装依赖。请先双击 setup-once.bat
  pause
  exit /b 1
)

set "PYTHONPATH=%cd%"
echo [前沿雷达] 采集进程已启动，会按间隔不停扫网。
echo 关闭本窗口即停止采集。
echo.
".venv\Scripts\python.exe" -m app.worker
echo.
echo 采集进程已退出。
pause
