@echo off
chcp 65001 >nul
title Building React UI for YouTube Farm Pro

echo =======================================================
echo   🛠️ BUILDING REACT SPA TO SERVER/STATIC
echo =======================================================
echo.

cd ui
call npm run build
cd ..

echo.
echo =======================================================
echo   ✅ BUILD HOÀN TẤT! Đã sẵn sàng chạy start_ui.bat
echo =======================================================
pause
