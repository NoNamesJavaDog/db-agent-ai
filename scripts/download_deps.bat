@echo off
chcp 65001 >nul
echo ========================================
echo   DB Agent - 下载离线依赖包
echo ========================================
echo.
echo 此脚本会下载所有依赖的 wheel 文件，
echo 用于在无网络环境下安装。
echo.

REM Navigate to project root
cd /d "%~dp0\.."

REM Create vendor directory
if not exist "vendor" mkdir "vendor"

echo [1/2] 下载依赖包到 vendor 目录...
pip download -r requirements.txt -d vendor --prefer-binary

if errorlevel 1 (
    echo.
    echo [错误] 下载失败！
    pause
    exit /b 1
)

echo [2/2] 创建离线安装脚本...

REM Create offline install script
(
echo @echo off
echo chcp 65001 ^>nul
echo echo 正在安装 DB Agent 依赖...
echo pip install --no-index --find-links=vendor -r requirements.txt
echo if errorlevel 1 ^(
echo     echo 安装失败！
echo     pause
echo     exit /b 1
echo ^)
echo echo.
echo echo 安装完成！
echo echo 运行方式: python main.py
echo pause
) > "install_offline.bat"

echo.
echo ========================================
echo   下载完成！
echo ========================================
echo.
echo 离线安装包内容:
echo   - vendor\          (依赖包目录)
echo   - requirements.txt (依赖清单)
echo   - install_offline.bat (离线安装脚本)
echo.
echo 使用方法:
echo   1. 将整个项目文件夹复制到目标机器
echo   2. 确保目标机器已安装 Python 3.8+
echo   3. 运行 install_offline.bat
echo   4. 编辑 config\config.ini
echo   5. 运行 python main.py
echo.
pause
