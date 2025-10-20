# Roadmap.sh Scraper

A Python CLI tool that extracts structured roadmap data from roadmap.sh and exports it to CSV format.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Extract engineering manager roadmap
python -m src.cli scrape

# Run in headless mode
python -m src.cli scrape --headless

# Custom output location
python -m src.cli scrape --output my_roadmap.csv
```

## What It Does

This tool automatically:

- Navigates to the roadmap.sh engineering manager page
- Extracts all visible roadmap topics with descriptions and resources
- Organizes data hierarchically (Category → Subcategory → Topic)
- Exports to CSV format for analysis

## Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd mindmapper
   ```

2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browser**
   ```bash
   playwright install chromium
   ```

## Usage

### Basic Usage

```bash
python -m src.cli scrape
```

### Options

- `--url TEXT` - Target URL (default: https://roadmap.sh/engineering-manager)
- `--output PATH` - Output CSV path (default: auto-generated with timestamp)
- `--delay-ms INT` - Delay between clicks in milliseconds (default: 500)
- `--headless` - Run browser in headless mode
- `--help` - Show help message

### Examples

```bash
# Extract with custom delay
python -m src.cli scrape --delay-ms 1000

# Save to specific location
python -m src.cli scrape --output ~/Downloads/em_roadmap.csv

# Run headless for automation
python -m src.cli scrape --headless --output /tmp/roadmap.csv
```

## Output Format

The tool generates a CSV file with the following columns:

- **Category** - Top-level roadmap category
- **Subcategory** - Mid-level grouping
- **Topic** - Individual learning topic
- **Description** - Topic description from the roadmap
- **Resources** - Pipe-separated list of resource URLs

Example output:

```csv
Category,Subcategory,Topic,Description,Resources
"Engineering Management","Team Building","Building High-Performing Teams","Learn how to create and maintain effective teams","https://example.com/team-building|https://example.com/performance"
```

## Troubleshooting

### Common Issues

**Browser doesn't start**

- Ensure Playwright is installed: `playwright install chromium`
- Check if you have a display available (for headed mode)

**Extraction fails**

- Try running with `--delay-ms 1000` for slower interactions
- Check your internet connection
- Verify the target URL is accessible

**Partial results**

- The tool continues processing even if some nodes fail
- Check the console output for specific error messages
- Partial results are still saved to CSV

### Getting Help

- Check the console output for detailed progress and error messages
- Review `docs/technical-design.md` for implementation details
- Open an issue for bugs or feature requests

## Development

See `docs/` directory for:

- `product-requirements.md` - Product goals and acceptance criteria
- `technical-design.md` - Architecture and implementation details
- `architecture-decisions.md` - Technical decision rationale

## License

[Add your license here]
