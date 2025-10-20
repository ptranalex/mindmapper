# Product Requirements Document (PRD)

## Roadmap.sh Scraper MVP

### Product Goal

Create a Python CLI tool that extracts the complete roadmap structure from https://roadmap.sh/engineering-manager and exports it to CSV format for analysis and documentation purposes.

### Problem Statement

The roadmap.sh engineering manager page contains valuable structured learning paths and resources, but this information is trapped in an interactive web interface. Users need a way to extract this data for:

- Personal study planning
- Team training curriculum development
- Documentation and analysis
- Integration with other tools

### Success Criteria

- **Primary**: Successfully extract 100% of visible roadmap topics with descriptions and resources
- **Secondary**: Export clean, structured CSV data
- **Tertiary**: CLI tool that's easy to use and maintain

### Acceptance Criteria

1. **Technology Stack**: Python-based solution
2. **Delivery Format**: MVP released as CLI tool
3. **Data Extraction**: Complete roadmap structure including:
   - Hierarchical categories and subcategories
   - Topic names and descriptions
   - Resource links
4. **Output Format**: CSV export (Google Sheets integration deferred)
5. **Reliability**: Handle client-rendered content and dynamic interactions

### User Stories

- **As a developer**, I want to extract roadmap data so I can create my own study plan
- **As a team lead**, I want to export roadmap content so I can share structured learning paths with my team
- **As a content creator**, I want to analyze roadmap structure so I can create complementary materials

### Technical Constraints

- Target site uses client-side rendering (no roadmap data in initial HTML)
- Interactive elements require browser automation
- Must handle dynamic overlays and modals
- Should be respectful of website resources (rate limiting)

### Out of Scope (MVP)

- Google Sheets integration
- Multiple roadmap support (frontend, backend, etc.)
- Resume from checkpoint functionality
- Async/parallel processing
- Advanced error recovery

### Future Enhancements

- Google Sheets API integration with `--gsheet` flag
- Support for other roadmap.sh paths (frontend, backend, DevOps)
- Resume capability for interrupted extractions
- Parallel drawer processing for improved performance
- Configuration file support for custom selectors

### Success Metrics

- **Completeness**: >95% of visible topics successfully extracted
- **Accuracy**: Correct hierarchical relationships maintained
- **Usability**: Single command execution with clear progress feedback
- **Reliability**: Handles edge cases gracefully (missing resources, failed drawers)

### Risk Mitigation

- **Site Changes**: Robust selector fallback chain
- **Rate Limiting**: Configurable delays between actions
- **Dynamic Content**: Wait strategies for content loading
- **Partial Failures**: Continue processing on individual node failures
