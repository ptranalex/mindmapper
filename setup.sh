#!/bin/bash
# Installation script for Roadmap Scraper

set -e

echo "=========================================="
echo "Roadmap Scraper - Installation"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
echo ""

# Activate virtual environment and install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt
echo ""

# Install Playwright browser
echo "Installing Playwright Chromium browser..."
playwright install chromium
echo ""

# Create output directory
echo "Creating output directory..."
mkdir -p output
echo ""

echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "To run the scraper:"
echo "  source venv/bin/activate"
echo "  python -m src.cli scrape"
echo ""
echo "For more options:"
echo "  python -m src.cli scrape --help"
echo ""

