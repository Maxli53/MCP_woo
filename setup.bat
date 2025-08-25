@echo off
echo ===============================================
echo    WooCommerce Management Suite Setup
echo ===============================================
echo.
echo This will set up both systems:
echo   1. Web Management Platform
echo   2. Claude Desktop MCP Server
echo.

:: Check Python 3.11
echo Checking Python 3.11...
py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Python 3.11 not found!
    echo Web Platform requires Python 3.11 for pandas/numpy
    echo.
    echo Checking fallback Python...
    python --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: No Python found!
        echo Please install Python 3.11 from:
        echo https://www.python.org/downloads/release/python-3119/
        pause
        exit /b 1
    )
    echo Found Python, but 3.11 is recommended for full functionality
    set PYTHON_CMD=python
) else (
    set PYTHON_CMD=py -3.11
)

:: Create virtual environment
if not exist "venv" (
    echo.
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv venv
)

:: Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate

:: Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install shared requirements
echo.
echo Installing shared requirements...
pip install -r shared\requirements\base.txt

:: Ask which system to set up
echo.
echo ===============================================
echo Which system would you like to set up?
echo   1. Both systems (recommended)
echo   2. Web Platform only
echo   3. Claude Desktop MCP only
echo ===============================================
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" goto :both
if "%choice%"=="2" goto :web
if "%choice%"=="3" goto :mcp
goto :invalid

:both
echo.
echo Setting up both systems...
call :setup_web
call :setup_mcp
goto :done

:web
echo.
echo Setting up Web Platform only...
call :setup_web
goto :done

:mcp
echo.
echo Setting up Claude Desktop MCP only...
call :setup_mcp
goto :done

:setup_web
echo.
echo ===============================================
echo Installing Web Platform requirements...
echo ===============================================
pip install -r shared\requirements\web.txt

:: Create web platform directories
if not exist "web-platform\data\stores" mkdir web-platform\data\stores
if not exist "web-platform\data\logs" mkdir web-platform\data\logs
if not exist "web-platform\data\backups" mkdir web-platform\data\backups

:: Create .env file if it doesn't exist
if not exist "web-platform\.env" (
    echo Creating web-platform\.env file...
    (
        echo # Web Platform Configuration
        echo PORT=8000
        echo HOST=0.0.0.0
        echo SECRET_KEY=change-this-to-a-random-string-%RANDOM%%RANDOM%
        echo ENCRYPTION_KEY=change-this-to-another-random-string-%RANDOM%%RANDOM%
        echo DATABASE_URL=sqlite:///data/stores.db
        echo LOG_LEVEL=INFO
    ) > web-platform\.env
)
echo Web Platform setup complete!
exit /b

:setup_mcp
echo.
echo ===============================================
echo Installing Claude Desktop MCP requirements...
echo ===============================================
pip install -r shared\requirements\mcp.txt

echo.
echo Claude Desktop MCP setup complete!
echo.
echo Next steps for Claude Desktop:
echo   1. Copy claude-desktop-mcp\config.example.json
echo   2. Update with your store credentials
echo   3. Add to %%APPDATA%%\Claude\claude_desktop_config.json
echo   4. Restart Claude Desktop
exit /b

:invalid
echo Invalid choice!
goto :done

:done
echo.
echo ===============================================
echo Setup Complete!
echo ===============================================
echo.
echo To start the Web Platform:
echo   cd web-platform
echo   start_webapp.bat
echo.
echo To test Claude Desktop MCP:
echo   cd claude-desktop-mcp
echo   test_mcp.bat
echo.
echo See README.md for more information
echo ===============================================
echo.
pause