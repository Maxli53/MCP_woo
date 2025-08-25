@echo off
echo ===============================================
echo    Testing Claude Desktop MCP Server
echo ===============================================
echo.

:: Check environment variables
if "%STORE_URL%"=="" (
    echo Setting test environment variables...
    set STORE_URL=https://your-store.com
    set WOOCOMMERCE_KEY=ck_test_key
    set WOOCOMMERCE_SECRET=cs_test_secret
    echo.
    echo NOTE: Using test credentials. Set real credentials:
    echo   set STORE_URL=https://your-actual-store.com
    echo   set WOOCOMMERCE_KEY=ck_your_actual_key
    echo   set WOOCOMMERCE_SECRET=cs_your_actual_secret
    echo.
)

:: Activate virtual environment
if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate
) else (
    echo ERROR: Virtual environment not found!
    echo Please run setup_mcp.bat first
    pause
    exit /b 1
)

echo Current configuration:
echo   STORE_URL: %STORE_URL%
echo   WOOCOMMERCE_KEY: %WOOCOMMERCE_KEY:~0,10%...
echo   WOOCOMMERCE_SECRET: %WOOCOMMERCE_SECRET:~0,10%...
echo.
echo Starting MCP server in test mode...
echo Press Ctrl+C to stop
echo ===============================================
echo.

:: Run the MCP server
python mcp_server_clean.py

pause