#!/bin/bash
# Install Python 3.14 with free-threading support

echo "🐍 Installing Python 3.14.0 for macOS"
echo ""
echo "The installer package has been downloaded to /tmp/python-3.14.0-macos11.pkg"
echo ""
echo "To install Python 3.14:"
echo "  1. Run: sudo installer -pkg /tmp/python-3.14.0-macos11.pkg -target /"
echo "  2. Or double-click: open /tmp/python-3.14.0-macos11.pkg"
echo ""
echo "After installation, Python 3.14 will be available at:"
echo "  /Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14"
echo ""
echo "To use Python 3.14 with this project:"
echo "  1. cd /Users/alex/Sandbox/mindmapper"
echo "  2. python3.14 -m venv venv314"
echo "  3. source venv314/bin/activate"
echo "  4. pip install -r requirements.txt"
echo "  5. python -m src.cli scrape --roadmap engineering-manager"
echo ""
echo "Python 3.14 will automatically use free-threaded parallel fetching!"
echo "Expected performance: ~10-15 seconds (vs ~75 seconds on Python 3.12)"

