@echo off
chcp 65001 >nul

if not "%CD%" == "%~dp0" (
    cd /d "%~dp0"
)

echo Starting Order Management System...
echo.

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrator permissions...
    powershell -Command "Start-Process cmd -ArgumentList '/c', 'cd /d ""%~dp0"" && ""%~f0""' -Verb RunAs"
    exit /b
)

netsh advfirewall firewall delete rule name="Python5000" dir=in >nul 2>&1
netsh advfirewall firewall add rule name="Python5000" dir=in action=allow protocol=TCP localport=5000 >nul 2>&1

if %errorLevel% equ 0 (
    echo Firewall configured successfully.
) else (
    echo Firewall configuration failed - local access still works.
)

echo.
echo Starting server...
echo Use admin@example.com with password admin123
echo Access locally at http://127.0.0.1:5000
echo Access from network at http://your-ip:5000
echo.
echo Press CTRL+C to stop server.
echo ===================================

python test_server.py runserver