@echo off
echo ===============================================
echo MCP WooCommerce Suite - Setup
echo ===============================================
echo.
echo Setting up with Python 3.11...
echo.

:: Create virtual environment with Python 3.11
if exist venv (
    echo Virtual environment already exists.
    set /p RECREATE="Recreate it? (y/n): "
    if /i "%RECREATE%"=="y" (
        rmdir /s /q venv
        py -3.11 -m venv venv
    )
) else (
    py -3.11 -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

:: Install requirements
echo.
echo Installing requirements...
pip install -r requirements.txt

echo.
echo ===============================================
echo Setup Complete!
echo ===============================================
echo.
echo To start the application, run:
echo   start.bat
echo.
pause