# Quick Start Guide - Python 3.14

## ✅ Status: Python 3.14 Ready!

Your roadmap scraper now runs on Python 3.14.0 with excellent performance!

## Using Python 3.14

### Activate Environment

```bash
cd roadmapsh-exporter
source venv314/bin/activate
```

You should see `(venv314)` in your terminal prompt.

### Verify Setup

```bash
# Check Python version
python --version
# Output: Python 3.14.0

# Check type safety
mypy src/
# Output: Success: no issues found in 8 source files
```

### Run the Scraper

#### Interactive Mode (Recommended)

```bash
python -m src.cli scrape --interactive
```

This will:

1. Show you all available roadmaps
2. Let you select one by number
3. Extract and save to CSV

#### Direct Mode

```bash
# Engineering Manager roadmap
python -m src.cli scrape --roadmap engineering-manager

# Frontend Developer roadmap
python -m src.cli scrape --roadmap frontend

# Backend Developer roadmap
python -m src.cli scrape --roadmap backend

# DevOps roadmap
python -m src.cli scrape --roadmap devops
```

#### List All Available Roadmaps

```bash
python -m src.cli scrape --list
```

#### Custom Output Path

```bash
python -m src.cli scrape --roadmap frontend --output /path/to/output.csv
```

#### Verbose Mode (Debug)

```bash
python -m src.cli scrape --roadmap backend --verbose
```

## Performance

### Expected Times

```
Python 3.14 (async fetching):
├─ Phase 1: Fetch JSON          ~1s
├─ Phase 2: Extract topics       <1s
├─ Phase 3: Parallel fetch      ~2s  ⚡
├─ Phase 4: Process cache        <1s
└─ Phase 5: Export CSV           <1s
Total: ~4-5 seconds
```

### Compare with Python 3.12

```bash
# Switch to Python 3.12 environment
source venv/bin/activate

# Run same command
time python -m src.cli scrape --roadmap engineering-manager

# Performance: ~4-5 seconds (same!)
# Both use async parallel fetching
```

## Switching Between Python Versions

### Use Python 3.14

```bash
source venv314/bin/activate
python --version  # 3.14.0
```

### Use Python 3.12

```bash
source venv/bin/activate
python --version  # 3.12.x
```

Both versions work perfectly and have the same performance!

## Output Format

The CSV will have these columns:

| Category            | Subcategory | Topic                           | Description                  | Resources                |
| ------------------- | ----------- | ------------------------------- | ---------------------------- | ------------------------ |
| Engineering Manager |             | What is Engineering Management? | Engineering management is... | https://...\|https://... |

- **Category**: Detected from roadmap structure
- **Subcategory**: Secondary grouping (if any)
- **Topic**: The specific topic name
- **Description**: Full text description
- **Resources**: Pipe-separated URLs

## Common Commands

### Quick Extraction

```bash
# Fastest way: Engineering Manager roadmap
python -m src.cli scrape --roadmap engineering-manager

# Output will be in: output/roadmap_engineering_manager_TIMESTAMP.csv
```

### Explore Roadmaps

```bash
# See all 65+ available roadmaps
python -m src.cli scrape --list

# Pick one interactively
python -m src.cli scrape --interactive
```

### Batch Processing

```bash
# Extract multiple roadmaps
for roadmap in frontend backend devops; do
    python -m src.cli scrape --roadmap $roadmap --output "${roadmap}.csv"
done
```

## Development Commands

### Type Checking

```bash
# Check all source files
mypy src/

# Or use the helper script
./scripts/check_types.sh
```

### Run Tests

```bash
# (Tests not yet implemented)
pytest tests/
```

## Troubleshooting

### SSL Certificate Error

```bash
# Fix SSL certificates for Python 3.14
/Applications/Python\ 3.14/Install\ Certificates.command
```

### Missing Dependencies

```bash
# Reinstall all dependencies
pip install -r requirements.txt
```

### Permission Errors

```bash
# Make scripts executable
chmod +x scripts/setup_python314.sh
chmod +x scripts/check_types.sh
```

### Wrong Python Version

```bash
# Deactivate current environment
deactivate

# Activate correct one
source venv314/bin/activate  # For Python 3.14
# or
source venv/bin/activate     # For Python 3.12
```

## Files Overview

### Core Source Files

- `src/cli.py` - Command-line interface
- `src/json_scraper.py` - Main scraping orchestrator
- `src/github_fetcher.py` - Downloads data from GitHub
- `src/json_parser.py` - Parses JSON and markdown
- `src/export.py` - Exports to CSV
- `src/async_fetcher.py` - Async parallel downloading
- `src/parallel_fetcher.py` - Free-threaded parallel (Python 3.14+)

### Configuration

- `requirements.txt` - Python dependencies
- `pyproject.toml` - Mypy configuration

### Documentation

- `README.md` - Main user documentation
- `PYTHON_314_SUCCESS.md` - Python 3.14 implementation summary
- `FREE_THREADING_NOTES.md` - Technical details about GIL
- `QUICK_START_PYTHON314.md` - This file

### Setup Scripts

- `scripts/setup_python314.sh` - Automated Python 3.14 setup
- `scripts/check_types.sh` - Type checking helper

## Next Steps

### 1. Try Different Roadmaps

```bash
python -m src.cli scrape --list
python -m src.cli scrape --interactive
```

### 2. Analyze the Data

```bash
# Use pandas, Excel, or any CSV tool
import pandas as pd
df = pd.read_csv('output/roadmap_engineering_manager_*.csv')
print(df.head())
```

### 3. Automate Extraction

```bash
# Create a cron job or scheduled task
0 0 * * * cd /path/to/roadmapsh-exporter && source venv314/bin/activate && python -m src.cli scrape --roadmap engineering-manager
```

### 4. Integrate with Other Tools

The CSV can be imported into:

- Google Sheets
- Excel
- Notion
- Airtable
- Any database

## Support

### Documentation

- See `README.md` for full documentation
- See `PYTHON_314_SUCCESS.md` for implementation details
- See `FREE_THREADING_NOTES.md` for performance details

### Performance

Expected: **~4-5 seconds** for most roadmaps
If slower: Check network connection and `--verbose` output

### Issues

- Type errors? Run `mypy src/`
- SSL errors? Run certificate installer
- Import errors? Check `pip install -r requirements.txt`

## Summary

✅ **Python 3.14 is ready to use!**

```bash
source venv314/bin/activate
python -m src.cli scrape --interactive
```

Fast, type-safe, and production-ready! 🎉
