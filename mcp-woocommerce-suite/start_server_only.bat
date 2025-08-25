@echo off
echo ===============================================
echo MCP WooCommerce Server - Direct Start
echo ===============================================
echo.

:: Activate virtual environment if exists
if exist venv (
    call venv\Scripts\activate.bat
)

:: Start only the MCP server
echo Starting MCP Server on port 8083...
python main.py --mode server

pause