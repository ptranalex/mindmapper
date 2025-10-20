# Browser-Based Scraper (Legacy)

This directory contains the original browser-based scraping implementation using Playwright.

## Why It Was Replaced

The browser-based approach was replaced with a GitHub JSON-based approach because:

1. **Anti-bot detection**: Roadmap.sh uses CloudFront and actively closes automated browser sessions
2. **Reliability issues**: Browser automation is fragile and prone to failures
3. **Performance**: Browser approach took 5-10 minutes vs 2 minutes for JSON approach
4. **Complexity**: Required Playwright installation and browser management
5. **System compatibility**: Headed mode had issues on some macOS configurations

## Original Components

- `browser.py` - Playwright browser management
- `nodes.py` - DOM node extraction with geometry-based hierarchy
- `drawer.py` - Interactive drawer content extraction
- `scraper.py` - Browser-based orchestration

## Lessons Learned

1. Always check if data is available through APIs or repositories first
2. Browser automation should be a last resort
3. Anti-bot detection is increasingly sophisticated
4. Simpler approaches (JSON parsing) are often more reliable

This code is preserved for reference and potential future use if needed.
