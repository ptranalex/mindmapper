# Architecture Decision Records (ADRs)

## Roadmap.sh Scraper MVP

### ADR-001: Browser Automation Framework

**Decision**: Use Playwright over Selenium
**Date**: 2024
**Status**: Accepted

**Context**: Need to automate browser interactions for client-rendered content extraction.

**Options Considered**:

- Selenium WebDriver
- Playwright
- Puppeteer (Node.js)
- Requests + BeautifulSoup (static only)

**Decision**: Playwright
**Rationale**:

- Better handling of modern web apps with client-side rendering
- More reliable wait strategies and element detection
- Built-in support for modern browser features
- Python bindings are mature and well-documented
- Better error handling and debugging capabilities

**Consequences**:

- Positive: More reliable extraction, better debugging
- Negative: Additional dependency, requires browser installation

### ADR-002: Hierarchy Detection Strategy

**Decision**: Geometry-based hierarchy inference over DOM structure analysis
**Date**: 2024
**Status**: Accepted

**Context**: The roadmap uses visual layout to convey hierarchy rather than semantic HTML structure.

**Options Considered**:

- DOM structure analysis (parent-child relationships)
- CSS class-based detection
- Geometry-based spatial analysis
- Manual configuration mapping

**Decision**: Geometry-based spatial analysis
**Rationale**:

- Visual layout is the primary hierarchy indicator
- DOM structure may not reflect visual relationships
- More robust to CSS changes and layout variations
- Can handle complex nested structures automatically

**Consequences**:

- Positive: Robust to layout changes, automatic hierarchy detection
- Negative: More complex algorithm, requires bounding box calculations

### ADR-003: Browser Mode Default

**Decision**: Headed mode by default, headless as option
**Date**: 2024
**Status**: Accepted

**Context**: Need to balance development experience with production efficiency.

**Options Considered**:

- Headless by default
- Headed by default
- Always headed
- Always headless

**Decision**: Headed by default with `--headless` option
**Rationale**:

- Easier debugging and development
- Users can see what's happening during extraction
- Headless mode available for automation/CI
- Better user experience for interactive debugging

**Consequences**:

- Positive: Better development experience, easier troubleshooting
- Negative: Slightly slower execution, requires display

### ADR-004: Error Handling Strategy

**Decision**: Skip failed nodes and continue processing
**Date**: 2024
**Status**: Accepted

**Context**: Individual node failures shouldn't stop the entire extraction process.

**Options Considered**:

- Fail fast on any error
- Retry failed nodes with exponential backoff
- Skip failed nodes and continue
- Manual intervention for failures

**Decision**: Skip failed nodes and continue processing
**Rationale**:

- Maximizes data extraction success
- Provides partial results even with some failures
- Simpler implementation for MVP
- User gets actionable feedback on what succeeded

**Consequences**:

- Positive: Higher success rate, partial results available
- Negative: May miss important data, requires manual review of failures

### ADR-005: Output Format

**Decision**: CSV-only for MVP, defer Google Sheets integration
**Date**: 2024
**Status**: Accepted

**Context**: Need to balance feature completeness with MVP delivery timeline.

**Options Considered**:

- CSV only
- Google Sheets only
- Both CSV and Google Sheets
- Multiple format options

**Decision**: CSV-only for MVP
**Rationale**:

- Faster MVP delivery
- CSV is universally compatible
- Google Sheets integration adds complexity (auth, API limits)
- Can be added as enhancement later

**Consequences**:

- Positive: Faster delivery, simpler implementation
- Negative: Manual step required for Google Sheets, less integrated experience
