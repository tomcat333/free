@echo off
cd /d "%~dp0"

echo [Frontier Radar] Checking whether .env is readable
echo Current dir: %cd%
echo.

if exist ".env" (
  echo Found: .env
) else if exist ".env.txt" (
  echo Found: .env.txt
  echo Please rename it to .env
) else (
  echo No .env found
  echo Copy .env.example to .env and fill your API key
)

echo.
if exist ".venv\Scripts\python.exe" (
  set "PYTHONPATH=%cd%"
  ".venv\Scripts\python.exe" -c "from app.config import settings; print('llm_enabled=', settings.llm_enabled); print('model=', settings.openai_model); print('base_url=', settings.openai_base_url); print('env_file=', settings.env_file_found or '(none)'); print('key_len=', len(settings.openai_api_key))"
) else (
  echo Missing .venv - run setup-once.bat first
)

echo.
pause
