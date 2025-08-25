@echo off
echo ===============================================
echo MCP WooCommerce Suite - Starting Application
echo ===============================================
echo.

:: Check if virtual environment exists
if not exist venv (
    echo ERROR: Virtual environment not found
    echo Please run install.bat first
    pause
    exit /b 1
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Start the application
echo Starting MCP WooCommerce Suite GUI...
python main.py --mode gui

:: If the GUI fails, offer to run in headless mode
if %errorlevel% neq 0 (
    echo.
    echo GUI failed to start. Would you like to run in headless mode? (Y/N)
    set /p choice=
    if /i "%choice%"=="Y" (
        echo Starting in headless mode...
        python main.py --headless
    )
)

pause