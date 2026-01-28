@echo off
chcp 65001 >nul
echo ========================================
echo   DB Agent - 打包工具
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装 PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [错误] PyInstaller 安装失败
        pause
        exit /b 1
    )
)

REM Navigate to project root
cd /d "%~dp0\.."

echo [1/3] 清理旧的构建文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo [2/3] 开始打包...
python -m PyInstaller build.spec --noconfirm

if errorlevel 1 (
    echo.
    echo [错误] 打包失败！
    pause
    exit /b 1
)

echo [3/3] 复制配置文件模板...
if not exist "dist\db-agent\config" mkdir "dist\db-agent\config"
copy "config\config.ini.example" "dist\db-agent\config\" >nul 2>&1
copy "config\config.ini" "dist\db-agent\config\config.ini.example" >nul 2>&1

echo.
echo ========================================
echo   打包完成！
echo ========================================
echo.
echo 输出目录: dist\db-agent\
echo.
echo 使用方法:
echo   1. 将 dist\db-agent 文件夹复制到目标机器
echo   2. 编辑 config\config.ini 配置数据库和 API Key
echo   3. 运行 db-agent.exe
echo.
pause
