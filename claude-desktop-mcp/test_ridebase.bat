@echo off
echo ===============================================
echo    Testing RideBase.fi MCP Connection
echo ===============================================
echo.

:: Set RideBase.fi credentials
set STORE_URL=https://ridebase.fi/
set WOOCOMMERCE_KEY=ck_f6ad7b402ad502bcccd39616c94717f282954278
set WOOCOMMERCE_SECRET=cs_9732d3b1cfe2db9fffd47316e99884efecac4b9c

:: Activate virtual environment
if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate
) else (
    echo ERROR: Virtual environment not found!
    echo Please run setup_mcp.bat first
    pause
    exit /b 1
)

echo Connecting to: %STORE_URL%
echo.
echo Starting MCP server for RideBase.fi...
echo Press Ctrl+C to stop
echo ===============================================
echo.

:: Run the MCP server
python mcp_server.py

pause