# Documentation Index

Welcome to the mindmapper documentation! This directory contains comprehensive documentation organized by topic.

## Quick Navigation

### 🚀 Getting Started

- **[Main README](../README.md)** - Project overview and basic usage
- **[Quick Start Guide](../QUICKSTART.md)** - Python 3.14 quick start

### 🎨 Design & Architecture

**Location**: [`design/`](design/)

Documentation about the product design and technical architecture:

- **[Product Requirements](design/product-requirements.md)** - Goals, success criteria, and acceptance criteria
- **[Technical Design](design/technical-design.md)** - System architecture and implementation approach
- **[Architecture Decisions](design/architecture-decisions.md)** - ADRs documenting key technical choices
- **[JSON Structure Analysis](design/json-structure-analysis.md)** - Analysis of roadmap.sh JSON format

### 🔧 Implementation Details

**Location**: [`implementation/`](implementation/)

Deep dive into how the scraper was built:

- **[Hierarchy Detection](implementation/hierarchy-detection.md)** - Proximity-based and graph-based algorithms
- **[Implementation Report](implementation/implementation-report.md)** - Complete implementation documentation
- **[Implementation Summary](implementation/implementation-summary.md)** - High-level implementation overview
- **[Batch Processing Complete](implementation/BATCH_PROCESSING_COMPLETE.md)** - Batch processing implementation summary
- **[Batch Processing Details](implementation/batch-processing.md)** - Comprehensive batch processing guide
- **[GenAI Enrichment](implementation/genai-enrichment.md)** - AI-powered CSV enrichment documentation
- **[How-To Column](implementation/HOW_TO_COLUMN_IMPLEMENTATION.md)** - How-To column implementation guide
- **[Changes Summary](implementation/CHANGES_SUMMARY.md)** - Detailed changes log
- **[Testing Guide](implementation/TESTING_GUIDE.md)** - Comprehensive testing guide for batch processing and enrichment

### 🐍 Python 3.14 Support

**Location**: [`python314/`](python314/)

Python 3.14 specific documentation:

- **[Setup Guide](python314/setup.md)** - Installation and configuration for Python 3.14
- **[Success Report](python314/success.md)** - Implementation results and performance
- **[Free-Threading Notes](python314/free-threading.md)** - Free-threading (PEP 779) details and benchmarks

### 🔍 Troubleshooting

**Location**: [`troubleshooting/`](troubleshooting/)

Common issues and their solutions:

- **[Subcategories](troubleshooting/subcategories.md)** - Why subcategories are empty for some roadmaps

### 📚 Legacy Documentation

**Location**: [`legacy/`](legacy/)

Archived documentation from the browser-based approach:

- **[Project Summary](legacy/PROJECT_SUMMARY.md)** - Summary of original browser-based implementation
- **[Testing Guide](legacy/TESTING.md)** - Testing documentation for browser-based scraper

## Documentation Standards

All documentation follows these principles:

1. **User-First** - Written for developers using the tool
2. **Clear Structure** - Organized by topic with clear navigation
3. **Code Examples** - Includes practical examples where relevant
4. **Up-to-Date** - Reflects current implementation (graph-based hierarchy)
5. **Comprehensive** - Covers design, implementation, and troubleshooting

## Contributing to Documentation

When adding or updating documentation:

- Place user-facing docs in the root directory
- Place technical docs in appropriate `docs/` subdirectories
- Update this README.md index when adding new files
- Follow markdown best practices (headings, code blocks, lists)
- Include examples and verification commands where helpful

## Quick Links by Role

### For Users

1. [Main README](../README.md) - Start here
2. [Quick Start](../QUICKSTART.md) - Get up and running
3. [Troubleshooting](troubleshooting/) - Solve common issues

### For Contributors

1. [Technical Design](design/technical-design.md) - Understand the architecture
2. [Implementation Details](implementation/) - See how it works
3. [Architecture Decisions](design/architecture-decisions.md) - Understand the "why"

### For Researchers

1. [Hierarchy Detection](implementation/hierarchy-detection.md) - Algorithm details
2. [Python 3.14 Performance](python314/success.md) - Benchmarks and results
3. [JSON Structure](design/json-structure-analysis.md) - Data format analysis

## Feedback

Found an issue with the documentation? Please update it or file an issue describing what's unclear or missing.
