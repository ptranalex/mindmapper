#!/bin/bash
# Automated setup script for Python 3.14 free-threading

set -e

echo "🐍 Setting up Python 3.14 Free-Threading Environment"
echo "===================================================="
echo ""

# Check if Python 3.14 is installed
if ! command -v python3.14 &> /dev/null; then
    echo "❌ Python 3.14 not found!"
    echo ""
    echo "Please install Python 3.14 first:"
    echo "  1. The installer should be open (or run: open /tmp/python-3.14.0-macos11.pkg)"
    echo "  2. Complete the installation wizard"
    echo "  3. Then run this script again"
    echo ""
    exit 1
fi

echo "✅ Python 3.14 found: $(python3.14 --version)"
echo ""

# Navigate to project directory
cd /Users/alex/Sandbox/mindmapper

# Create Python 3.14 virtual environment
echo "📦 Creating Python 3.14 virtual environment..."
python3.14 -m venv venv314
echo "✅ Virtual environment created: venv314/"
echo ""

# Activate and install dependencies
echo "📥 Installing dependencies..."
source venv314/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Verify installation
echo "🔍 Verifying installation..."
python --version
echo "Python location: $(which python)"
echo ""

# Check free-threading
echo "🧵 Checking free-threading support..."
python -c "
import sys
free_threading = not getattr(sys, '_is_gil_enabled', lambda: True)()
print(f'Free-threading available: {free_threading}')
if free_threading:
    print('✅ GIL is DISABLED - true parallel execution enabled!')
else:
    print('⚠️  GIL is present - will use async fallback')
"
echo ""

# Run type checking
echo "🔎 Running type checks..."
mypy src/ && echo "✅ Type checking passed!"
echo ""

echo "===================================================="
echo "🎉 Setup complete!"
echo ""
echo "To use Python 3.14:"
echo "  source venv314/bin/activate"
echo ""
echo "To run the scraper:"
echo "  python -m src.cli scrape --roadmap engineering-manager"
echo ""
echo "Expected performance with free-threading:"
echo "  ~10-12 seconds (vs ~75s sequential)"
echo ""
echo "The scraper will automatically use free-threaded parallel"
echo "fetching for maximum performance!"
echo "===================================================="

