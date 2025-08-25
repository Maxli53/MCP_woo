@echo off
echo ===============================================
echo MCP WooCommerce Suite
echo ===============================================
echo.

:: Activate virtual environment
if not exist venv (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

:: Clear port 8000 if in use
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000"') do (
    taskkill /F /PID %%a 2>nul
)

:: Open browser
echo Opening browser at http://localhost:8000
start http://localhost:8000

:: Start web server
echo.
echo Starting web server...
echo Press Ctrl+C to stop
echo.
python web_server.py

pause