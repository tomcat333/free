@echo off
chcp 65001 >nul
echo 正在结束前沿雷达相关进程（uvicorn / worker）...
taskkill /FI "WINDOWTITLE eq 前沿雷达-网页*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq 前沿雷达-采集*" /T /F >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8787" ^| findstr "LISTENING"') do (
  taskkill /PID %%p /F >nul 2>&1
)
echo 已尝试停止。若窗口还在，可直接点右上角关闭。
pause
