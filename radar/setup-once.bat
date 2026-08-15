@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [前沿雷达] 首次安装：创建虚拟环境并安装依赖
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo 找不到 python。请先安装 Python 3，并勾选 “Add python.exe to PATH”。
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo 正在创建 .venv ...
  python -m venv .venv
  if errorlevel 1 (
    echo 创建虚拟环境失败。
    pause
    exit /b 1
  )
)

echo 正在安装依赖（可能要一两分钟）...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo 依赖安装失败。
  pause
  exit /b 1
)

echo.
echo 安装完成。以后日常请双击 start-all.bat
pause
