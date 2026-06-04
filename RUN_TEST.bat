@echo off
chcp 65001 >nul
title E2E Test - Nuoi Kenh YouTube
cd /d "%~dp0"

echo ============================================
echo   E2E Test - Nuoi Kenh YouTube
echo ============================================
echo.

python tests\test_e2e.py

echo.
pause >nul
