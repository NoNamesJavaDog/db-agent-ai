#!/bin/bash
echo "========================================"
echo "  DB Agent - Build Package Tool"
echo "========================================"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "[Error] Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" &> /dev/null; then
    echo "[Info] Installing PyInstaller..."
    pip3 install pyinstaller
    if [ $? -ne 0 ]; then
        echo "[Error] Failed to install PyInstaller"
        exit 1
    fi
fi

# Navigate to project root
cd "$(dirname "$0")/.."

echo "[1/3] Cleaning old build files..."
rm -rf build dist

echo "[2/3] Building package..."
python3 -m PyInstaller build.spec --noconfirm

if [ $? -ne 0 ]; then
    echo
    echo "[Error] Build failed!"
    exit 1
fi

echo "[3/3] Copying config templates..."
mkdir -p dist/db-agent/config
cp config/config.ini.example dist/db-agent/config/ 2>/dev/null || true
cp config/config.ini dist/db-agent/config/config.ini.example 2>/dev/null || true

echo
echo "========================================"
echo "  Build Complete!"
echo "========================================"
echo
echo "Output directory: dist/db-agent/"
echo
echo "Usage:"
echo "  1. Copy the dist/db-agent folder to target machine"
echo "  2. Edit config/config.ini with database and API settings"
echo "  3. Run ./db-agent"
echo
