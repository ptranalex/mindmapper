# Roadmap.sh Scraper - Technical Design

## Architecture Overview

CLI tool using Playwright (Python) to scrape client-rendered roadmap, extract hierarchical structure via DOM + geometry analysis, and export to CSV.

## Project Structure

```
mindmapper/
├── requirements.txt          # Dependencies: playwright, click, pandas
├── README.md                 # User-facing: quick start, installation, usage examples
├── docs/
│   ├── product-requirements.md  # Product requirements: goal, acceptance criteria, user stories, success metrics, out of scope
│   ├── technical-design.md  # This document: architecture & implementation details
│   └── architecture-decisions.md  # Why Playwright, geometry-based hierarchy, etc.
├── src/
│   ├── __init__.py
│   ├── cli.py               # Entry point with Click CLI
│   ├── scraper.py           # Main orchestration logic
│   ├── browser.py           # Playwright browser management
│   ├── nodes.py             # Node extraction & geometry classification
│   ├── drawer.py            # Drawer interaction & content extraction
│   └── export.py            # CSV export logic
└── output/                   # Default output directory (git-ignored)
```

## Documentation Structure

Following industry best practices:

- **README.md** (root) - User-facing documentation: what it does, installation, quick start, CLI usage
- **docs/product-requirements.md** - Product requirements: goal, acceptance criteria, user stories, success metrics, out of scope
- **docs/technical-design.md** - Developer-facing: architecture overview, component details, algorithms, implementation notes
- **docs/architecture-decisions.md** - Context on key technical decisions (why Playwright over Selenium, why geometry-based hierarchy inference, why headed by default, CSV-only for MVP)

## Core Components

### 1. Browser Management (`browser.py`)

- Launch Playwright with desktop user-agent (headed by default)
- Navigate to target URL with network idle wait
- Dismiss overlays: cookie banners, marketing popups (try common selectors)
- Wait for roadmap canvas to render (detect SVG or container with scroll)

### 2. Node Extraction (`nodes.py`)

**Selector Strategy** (fallback chain):

1. `svg g:has(rect):has(text)` - SVG-based nodes
2. `[data-node-id]`, `[data-type="topic"]` - data attributes
3. `.node`, `[role="button"]` within roadmap container

**Scroll & Collection**:

- Full-page vertical scroll in ~100vh increments
- For each viewport: extract visible nodes with `element.bounding_box()`
- Dedupe by `(text, x, y, w, h)` tuple across scrolls
- Sort final list by (y, x) for top-to-bottom, left-to-right order

### 3. Hierarchy Inference (`nodes.py`)

**Classification**:

- **Container** (category/subcategory): Large rect (width > 300px OR height > 150px), has header text
- **Leaf** (topic): Small rounded rect, typically clickable

**Nesting Algorithm**:

1. For each leaf, find containers that fully enclose it (with 3px tolerance)
2. Assign to smallest enclosing container
3. Nest containers recursively (subcategory inside category)
4. Fallback: if no enclosure, attach to nearest header above with overlapping x-range

### 4. Drawer Extraction (`drawer.py`)

**For each topic node** (in sorted order):

1. Scroll element into view
2. Click and wait for drawer (race conditions):

   - `[role="dialog"]`
   - `aside[aria-modal="true"]`
   - Heading element change

3. Extract **Topic**: drawer heading (h1/h2), fallback to tile label
4. Extract **Description**: all `<p>` tags in Overview section, join with space
5. Extract **Resources**:

   - Look for "Resources" tab/button, click if found
   - Collect all `a[href]` elements: extract `href` only
   - Join URLs with pipe `|`

6. Close drawer (X button, ESC key, or backdrop click)
7. On failure: log warning, skip node, continue

### 5. Export (`export.py`)

**CSV Schema**:

```
Category, Subcategory, Topic, Description, Resources
```

- Use pandas DataFrame for clean CSV generation
- UTF-8 encoding, quote all fields
- Save to `output/roadmap_engineering_manager_{timestamp}.csv`

### 6. CLI (`cli.py`)

```bash
python -m src.cli scrape [OPTIONS]

Options:
  --url TEXT           Target URL [default: https://roadmap.sh/engineering-manager]
  --output PATH        Output CSV path [default: auto-generated]
  --delay-ms INT       Delay between clicks in ms [default: 500]
  --headless          Run browser in headless mode
  --help              Show this message and exit
```

## Key Implementation Details

**Resilience**:

- 3px bbox expansion for containment checks (geometry tolerance)
- Random jitter on delays (delay-ms ± 20%)
- Graceful skip on drawer timeout (5s wait max)
- Log progress: "Processing node 15/87: Topic Name"

**Performance**:

- Single browser context reuse
- Parallel-safe (synchronous for MVP, but structure allows async later)
- Estimated time: ~5-10 minutes for typical roadmap (100+ nodes)

**Error Handling**:

- Try/except per node with continue on failure
- Final summary: "Successfully extracted 82/87 nodes"
- Save partial results even if interrupted

## Dependencies

```txt
playwright==1.40.0
click==8.1.7
pandas==2.1.4
```

Post-install: `playwright install chromium`

## Testing Strategy (Manual for MVP)

1. Run headed mode, observe first 5 nodes
2. Verify CSV output has all columns
3. Spot-check: category nesting correct, resources present
4. Edge case: drawer with no resources tab

## Future Enhancements (Out of Scope)

- Google Sheets integration with gspread
- Async/parallel drawer extraction
- Multiple roadmap support (frontend, backend, etc.)
- Resume from checkpoint on crash
