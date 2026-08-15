@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [前沿雷达] 检查 .env 是否会被读到
echo 当前目录: %cd%
echo.

if exist ".env" (
  echo 找到: .env
) else if exist ".env.txt" (
  echo 找到: .env.txt
  echo 请把它改名为 .env （去掉 .txt）
) else (
  echo 没有找到 .env
  echo 请把 .env.example 复制为 .env 后再填 Key
)

echo.
if exist ".venv\Scripts\python.exe" (
  set "PYTHONPATH=%cd%"
  ".venv\Scripts\python.exe" -c "from app.config import settings; print('llm_enabled=', settings.llm_enabled); print('model=', settings.openai_model); print('base_url=', settings.openai_base_url); print('env_file=', settings.env_file_found or '(none)'); print('key_len=', len(settings.openai_api_key))"
) else (
  echo 还没有 .venv，请先双击 setup-once.bat
)

echo.
pause
