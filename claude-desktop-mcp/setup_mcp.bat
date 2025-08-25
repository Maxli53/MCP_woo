@echo off
echo ===============================================
echo    Setting up Claude Desktop MCP Server
echo ===============================================
echo.

:: Check Python
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.8+ and add to PATH
    pause
    exit /b 1
)

:: Create virtual environment if needed
if not exist "..\venv" (
    echo Creating virtual environment...
    python -m venv ..\venv
)

:: Activate virtual environment
echo Activating virtual environment...
call ..\venv\Scripts\activate

:: Install minimal requirements
echo Installing MCP requirements...
pip install mcp woocommerce httpx

echo.
echo ===============================================
echo Setup complete!
echo.
echo Next steps:
echo   1. Copy config.example.json to your Claude Desktop config location:
echo      %%APPDATA%%\Claude\claude_desktop_config.json
echo.
echo   2. Update the config with:
echo      - Your actual file paths
echo      - WooCommerce store URL
echo      - WooCommerce API keys
echo.
echo   3. Restart Claude Desktop
echo.
echo The MCP server will run automatically when Claude Desktop starts.
echo ===============================================
echo.
pause