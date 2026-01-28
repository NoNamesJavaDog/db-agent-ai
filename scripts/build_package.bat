@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo   DB Agent - Build Package Tool
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [Info] Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [Error] Failed to install PyInstaller
        pause
        exit /b 1
    )
)

REM Navigate to project root
cd /d "%~dp0\.."

echo [1/3] Cleaning old build files...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo [2/3] Building package...
python -m PyInstaller build.spec --noconfirm

if errorlevel 1 (
    echo.
    echo [Error] Build failed!
    pause
    exit /b 1
)

echo [3/3] Copying config files...
if not exist "dist\db-agent\config" mkdir "dist\db-agent\config"
if exist "config\config.ini" copy "config\config.ini" "dist\db-agent\config\" >nul 2>&1
if exist "config\config.ini.example" copy "config\config.ini.example" "dist\db-agent\config\" >nul 2>&1

echo.
echo ========================================
echo   Build Complete!
echo ========================================
echo.
echo Output: dist\db-agent\
echo.
echo Usage:
echo   1. Copy dist\db-agent folder to target machine
echo   2. Edit config\config.ini
echo   3. Run db-agent.exe
echo.
pause
