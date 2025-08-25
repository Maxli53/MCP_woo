@echo off
echo ===============================================
echo MCP WooCommerce Suite - Installation Script
echo ===============================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)

:: Check for Node.js (required for LocalTunnel)
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Node.js is not installed
    echo LocalTunnel features will not be available
    echo Install Node.js from https://nodejs.org for full functionality
    echo.
    pause
)

echo [1/6] Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/6] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/6] Upgrading pip...
python -m pip install --upgrade pip

echo [4/6] Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    echo Please check requirements.txt and try again
    pause
    exit /b 1
)

echo [5/6] Installing LocalTunnel (if Node.js is available)...
where node >nul 2>&1
if %errorlevel% equ 0 (
    npm install -g localtunnel
    echo LocalTunnel installed successfully
) else (
    echo Skipping LocalTunnel installation (Node.js not found)
)

echo [6/6] Setting up configuration...
if not exist .env (
    copy .env.example .env
    echo Created .env file - Please edit it with your settings
)

:: Create necessary directories
mkdir data 2>nul
mkdir data\logs 2>nul
mkdir data\backups 2>nul
mkdir data\stores 2>nul
mkdir data\exports 2>nul

echo.
echo ===============================================
echo Installation completed successfully!
echo ===============================================
echo.
echo Next steps:
echo 1. Edit .env file with your configuration
echo 2. Run 'start.bat' to launch the application
echo 3. Access the GUI to add your WooCommerce stores
echo.
echo For documentation, visit the docs folder
echo.
pause