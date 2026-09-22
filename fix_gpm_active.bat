@echo off
chcp 65001 >nul
title Fix GPM Active - DNS & Hosts

:: Tu dong xin quyen Administrator neu chua co
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Đang yêu cầu quyền Administrator...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

echo ===================================================
echo   TIẾN HÀNH SỬA DNS VÀ CẬP NHẬT FILE HOSTS CHO GPM
echo ===================================================
echo.

:: 1. Cấu hình DNS Google (8.8.8.8, 8.8.4.4) cho tất cả card mạng IPv4 đang kết nối
echo [1/3] Đang cấu hình DNS Google (8.8.8.8, 8.8.4.4)...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | ForEach-Object { " ^
    "   Set-DnsClientServerAddress -InterfaceIndex $_.ifIndex -ServerAddresses ('8.8.8.8','8.8.4.4') -ErrorAction SilentlyContinue; " ^
    "   Write-Host ('  + Da doi DNS cho card: ' + $_.Name); " ^
    "}"

:: 2. Thêm domain vào file hosts
echo.
echo [2/3] Đang cập nhật file hosts (C:\Windows\System32\drivers\etc\hosts)...
set "HOSTS_PATH=%windir%\System32\drivers\etc\hosts"

:: Bỏ thuộc tính Read-only nếu có
attrib -r "%HOSTS_PATH%" >nul 2>&1

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$path = '%HOSTS_PATH%';" ^
    "$content = [System.IO.File]::ReadAllText($path);" ^
    "$entries = @(" ^
    "   '127.0.0.1 api.nhhtool.id.vn'," ^
    "   '127.0.0.1 nhhtool.id.vn'," ^
    "   '0.0.0.0 gpmloginpserver.com'," ^
    "   '0.0.0.0 www.gpmloginpserver.com'" ^
    ");" ^
    "$added = 0;" ^
    "foreach ($e in $entries) {" ^
    "   $domain = $e.Split(' ')[1];" ^
    "   if ($content -notmatch [regex]::Escape($domain)) {" ^
    "       $content += [Environment]::NewLine + $e;" ^
    "       $added++;" ^
    "       Write-Host ('  + Da them: ' + $e);" ^
    "   } else {" ^
    "       Write-Host ('  * Da ton tai: ' + $domain);" ^
    "   }" ^
    "};" ^
    "if ($added -gt 0) { [System.IO.File]::WriteAllText($path, $content); }"

:: 3. Xoá cache DNS
echo.
echo [3/3] Đang làm mới cache DNS hệ thống...
ipconfig /flushdns >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "Clear-DnsClientCache" >nul 2>&1

echo.
echo ===================================================
echo   HOÀN TẤT! ĐÃ SỬA XONG DNS VÀ FILE HOSTS.
echo   Bây giờ bạn có thể mở lại Active VoThuong.exe.
echo ===================================================
echo.
pause
