@echo off
echo ===============================================
echo    Setting up Web Management Platform
echo ===============================================
echo.

:: Check Python 3.11
echo Checking Python version...
py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.11 not found!
    echo Please install Python 3.11 from:
    echo https://www.python.org/downloads/release/python-3119/
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "..\venv" (
    echo Creating virtual environment...
    py -3.11 -m venv ..\venv
)

:: Activate virtual environment
echo Activating virtual environment...
call ..\venv\Scripts\activate

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install requirements
echo Installing requirements...
pip install fastapi uvicorn pandas numpy openpyxl woocommerce httpx python-multipart jinja2 aiofiles python-dotenv cryptography PyQt6

:: Create data directories
echo Creating data directories...
if not exist "data\stores" mkdir data\stores
if not exist "data\logs" mkdir data\logs
if not exist "data\backups" mkdir data\backups

:: Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file...
    (
        echo # Web Platform Configuration
        echo PORT=8000
        echo HOST=0.0.0.0
        echo SECRET_KEY=change-this-to-a-random-string
        echo ENCRYPTION_KEY=change-this-to-another-random-string
        echo DATABASE_URL=sqlite:///data/stores.db
        echo LOG_LEVEL=INFO
    ) > .env
    echo.
    echo IMPORTANT: Edit .env file to set your secret keys!
)

echo.
echo ===============================================
echo Setup complete!
echo.
echo Next steps:
echo   1. Edit .env file with your configuration
echo   2. Run start_webapp.bat to launch the server
echo ===============================================
echo.
pause