@echo off
echo Adding firewall rule for Python server...
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges...
) else (
    echo ERROR: This script requires administrator privileges!
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Delete existing rule (if any)
echo Removing existing firewall rule...
netsh advfirewall firewall delete rule name="Python 5000" dir=in >nul 2>&1

REM Add new firewall rule
echo Adding new firewall rule for port 5000...
netsh advfirewall firewall add rule name="Python 5000" dir=in action=allow protocol=TCP localport=5000

if %errorLevel% == 0 (
    echo.
    echo SUCCESS: Firewall rule added successfully!
    echo Port 5000 is now allowed through Windows Firewall.
    echo.
    echo You can now access the server from other computers on the network:
    echo Local access: http://127.0.0.1:5000
    echo Network access: http://[YOUR_IP]:5000
    echo.
) else (
    echo.
    echo ERROR: Failed to add firewall rule!
    echo Please check Windows Firewall settings manually.
    echo.
)

echo Press any key to exit...
pause >nul