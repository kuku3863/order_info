@echo off
chcp 65001 >nul
echo Fixing network access...

REM Check admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Need admin privileges, restarting...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

REM Add firewall rule
netsh advfirewall firewall delete rule name="Python 5000" dir=in >nul 2>&1
netsh advfirewall firewall add rule name="Python 5000" dir=in action=allow protocol=TCP localport=5000

if %errorLevel% == 0 (
    echo Network access fixed! Others can now access your server.
) else (
    echo Failed to configure firewall. Please manually add port 5000 inbound rule.
)

echo.
echo Server address: http://YOUR_IP:5000
echo Login: admin@example.com / admin123
echo.
pause