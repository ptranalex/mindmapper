# Testing Guide

## Pre-Flight Checklist

All components have been implemented and the CLI is operational:

- ✅ Project structure created
- ✅ Dependencies installed (playwright, click, pandas)
- ✅ Virtual environment configured
- ✅ Playwright browser installed
- ✅ CLI help command works

## Manual Testing Instructions

### 1. Quick Smoke Test (Recommended First)

Test the scraper on a small subset by interrupting after a few nodes:

```bash
source venv/bin/activate
python -m src.cli scrape --verbose
# Press Ctrl+C after 3-5 nodes are processed
# Check output/ directory for partial CSV
```

**Expected behavior:**

- Browser opens in headed mode
- Navigates to roadmap.sh/engineering-manager
- Console shows progress: "Processing node 1/X: Topic Name"
- Partial CSV is saved even after interrupt

### 2. Full End-to-End Test

Run the complete scraper (takes 5-10 minutes):

```bash
source venv/bin/activate
python -m src.cli scrape
```

**Expected output:**

```
============================================================
Starting roadmap scraping process
URL: https://roadmap.sh/engineering-manager
Headless: False
Delay: 500ms
============================================================

... (navigation and setup logs) ...

============================================================
Phase 1: Node Extraction
============================================================
... (scroll and collection logs) ...
Extracted N unique nodes after deduplication

============================================================
Phase 2: Hierarchy Inference
============================================================
Found X containers and Y leaf nodes
Assigned hierarchy to Y/Y leaf nodes

============================================================
Phase 3: Drawer Content Extraction
============================================================
Processing node 1/Y: Topic Name
  ✓ Extracted successfully
Processing node 2/Y: Another Topic
  ✓ Extracted successfully
...

============================================================
Phase 4: Export to CSV
============================================================
Exporting Y rows to output/roadmap_engineering_manager_TIMESTAMP.csv

============================================================
SCRAPING COMPLETE
============================================================
Total nodes found: N
Leaf nodes (topics): Y
Successfully extracted: Y/Y
Success rate: 100.0%
Output file: output/roadmap_engineering_manager_TIMESTAMP.csv
============================================================

✓ Scraping completed successfully!
Output file: output/roadmap_engineering_manager_TIMESTAMP.csv
```

### 3. Verify CSV Output

Check the generated CSV file:

```bash
# View first few rows
head -20 output/roadmap_engineering_manager_*.csv

# Count rows
wc -l output/roadmap_engineering_manager_*.csv

# Open in spreadsheet application
open output/roadmap_engineering_manager_*.csv
```

**CSV Quality Checklist:**

- [ ] All 5 columns present: Category, Subcategory, Topic, Description, Resources
- [ ] No empty rows
- [ ] Categories are properly assigned (not "Uncategorized")
- [ ] Descriptions contain actual content
- [ ] Resources are pipe-separated URLs
- [ ] UTF-8 encoding (special characters display correctly)
- [ ] Hierarchical structure makes sense

### 4. Test Headless Mode

Run in headless mode (no browser window):

```bash
source venv/bin/activate
python -m src.cli scrape --headless
```

**Expected:** Same output, but no visible browser window.

### 5. Test Custom Options

```bash
# Custom output path
python -m src.cli scrape --output ~/Desktop/my_roadmap.csv

# Slower delays (more conservative)
python -m src.cli scrape --delay-ms 1000

# Different roadmap (if structure is similar)
python -m src.cli scrape --url https://roadmap.sh/frontend
```

## Known Limitations & Edge Cases

### Expected Behavior

1. **Partial Failures:** Some nodes may fail to extract (drawer timeout, no resources). This is expected and the tool continues processing.
2. **Success Rate:** Expect 90-100% success rate. < 90% indicates site structure changes.

3. **Extraction Time:** ~5-10 minutes for ~100 topics at 500ms delay.

### Troubleshooting

**Browser doesn't open:**

```bash
playwright install chromium
```

**Import errors:**

```bash
source venv/bin/activate  # Ensure venv is activated
pip install -r requirements.txt
```

**Site structure changed:**

- Check `--verbose` output for selector failures
- Update selector chains in `nodes.py` and `drawer.py`
- May need to adjust `CONTAINER_WIDTH_THRESHOLD` values

**Low success rate:**

- Increase delay: `--delay-ms 1000`
- Check internet connection
- Verify site is accessible

## Automated Testing (Future)

For CI/CD integration, create:

- Unit tests for node classification logic
- Mock Playwright responses for drawer extraction
- Integration test with known roadmap snapshot
- Schema validation for CSV output

## Reporting Issues

When reporting issues, include:

1. Complete console output with `--verbose` flag
2. Generated CSV file (if created)
3. Python version: `python --version`
4. OS: `uname -a`
5. Screenshot of browser (if headed mode)
