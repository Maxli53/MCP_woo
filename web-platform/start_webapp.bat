@echo off
echo ===============================================
echo    WooCommerce Web Management Platform
echo ===============================================
echo.

:: Check if virtual environment exists
if not exist "..\venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run setup_webapp.bat first
    pause
    exit /b 1
)

:: Activate virtual environment
call ..\venv\Scripts\activate

:: Clear port 8000 if in use
echo Clearing port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /F /PID %%a 2>nul
)

:: Create data directories if they don't exist
if not exist "data\stores" mkdir data\stores
if not exist "data\logs" mkdir data\logs
if not exist "data\backups" mkdir data\backups

:: Start the web server
echo.
echo Starting web server...
echo ===============================================
echo.
echo Web interface will be available at:
echo   http://localhost:8000
echo.
echo API documentation available at:
echo   http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo ===============================================
echo.

:: Run the web server
python web_server.py

pause