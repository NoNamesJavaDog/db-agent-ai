@echo off
chcp 65001 >nul
REM DB Agent Startup Script (Windows)

set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..

echo ======================================
echo   DB Agent - AI Database Assistant
echo ======================================
echo.

REM Change to project directory
cd /d "%PROJECT_DIR%"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found
    echo Please install Python 3.8+: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Python check passed
echo.

REM Check virtual environment
if exist ".venv\Scripts\activate.bat" (
    echo [2/3] Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [2/3] Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
)

REM Install dependencies
echo [3/3] Checking and installing dependencies...
pip install -q -r requirements.txt 2>nul
echo.

REM Check config file
if not exist "config\config.ini" (
    echo [Warning] Config file not found: config\config.ini
    echo Please create the config file with database and API settings
    pause
    exit /b 1
)

echo ======================================
echo   Config file: config\config.ini
echo   Edit this file to modify database or API settings
echo ======================================
echo.

REM Start CLI
echo Starting DB Agent...
echo.
python main.py

pause
