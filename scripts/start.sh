#!/bin/bash
# DB Agent Startup Script (Linux/macOS)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "  DB Agent - AI Database Assistant"
echo "======================================"
echo ""

# Change to project directory
cd "$PROJECT_DIR"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ [Error] Python3 not found"
    echo "Please install Python 3.8+"
    exit 1
fi

echo "✓ [1/3] Python check passed"
echo ""

# Check virtual environment
if [ -d ".venv" ]; then
    echo "✓ [2/3] Activating virtual environment..."
    source .venv/bin/activate
else
    echo "○ [2/3] Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# Install dependencies
echo "○ [3/3] Checking and installing dependencies..."
pip install -q -r requirements.txt 2>/dev/null
echo ""

# Check config file
if [ ! -f "config/config.ini" ]; then
    echo "⚠️  [Warning] Config file not found: config/config.ini"
    echo "Please create the config file with database and API settings"
    exit 1
fi

echo "======================================"
echo "  Config file: config/config.ini"
echo "  Edit this file to modify database or API settings"
echo "======================================"
echo ""

# Start CLI
echo "Starting DB Agent..."
echo ""
python3 main.py
