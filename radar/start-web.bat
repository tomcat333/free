@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo 还没有安装依赖。请先双击 setup-once.bat
  pause
  exit /b 1
)

set "PYTHONPATH=%cd%"
set "PORT=8787"
echo [前沿雷达] 网页服务：http://127.0.0.1:%PORT%
if exist ".env" (
  echo [配置] 已找到 .env
) else if exist ".env.txt" (
  echo [警告] 找到的是 .env.txt，请改名为 .env
) else (
  echo [警告] 当前目录没有 .env，深度介绍会不可用
)
echo 关闭本窗口即停止网页服务。
echo.
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port %PORT%
echo.
echo 网页服务已退出。
pause
