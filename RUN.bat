@echo off
chcp 65001 >nul
title Nuoi Kenh YouTube - GPM Login
cd /d "%~dp0"

echo ============================================
echo   Nuoi Kenh YouTube - GPM Login
echo   Nhan Ctrl+C de dung script
echo ============================================
echo.

python main.py

echo.
echo ============================================
echo   Script da ket thuc. Nhan phim bat ky...
echo ============================================
pause >nul
