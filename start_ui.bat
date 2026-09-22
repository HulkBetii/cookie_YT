@echo off
chcp 65001 >nul
title YouTube Farm Pro — Control Station Dashboard

echo =======================================================
echo   ⚡ YOUTUBE FARM PRO — CONTROL DASHBOARD (US MARKET)
echo =======================================================
echo.
echo [1/2] Đang khởi động FastAPI Server ^& WebSocket Hub...
echo [2/2] Tự động mở giao diện tại: http://localhost:8000
echo.
echo Nhấn Ctrl+C để dừng server.
echo =======================================================
echo.

py -3.12 server/app.py --port 8000 --open

pause
