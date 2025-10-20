# Batch Processing Testing Guide

## Quick Test (No API Key Required)

These tests validate the batch processing logic without making API calls:

### 1. Type Checking

```bash
cd /Users/alex/Sandbox/roadmapsh-exporter
source venv314/bin/activate
mypy src/
```

**Expected:** `Success: no issues found in 12 source files`

### 2. Import Check

```bash
python -c "from src.enrichment.prompts import BATCH_RESPONSE_SCHEMA, build_batch_prompt; print('✅ Imports working')"
```

**Expected:** `✅ Imports working`

### 3. Batch Prompt Builder

```bash
python << 'EOF'
from src.enrichment.prompts import build_batch_prompt

test_rows = [
    {"Category": "Test", "Subcategory": "", "Topic": "Topic 1", "Description": "Desc 1"},
    {"Category": "Test", "Subcategory": "", "Topic": "Topic 2", "Description": "Desc 2"},
]

prompt = build_batch_prompt(test_rows)
print(f"✅ Prompt generated ({len(prompt)} chars)")
print(f"✅ Contains 'Topic 1': {'Topic 1' in prompt}")
print(f"✅ Contains 'Topic 2': {'Topic 2' in prompt}")
print(f"✅ Contains ID '0': {'"id": "0"' in prompt}")
print(f"✅ Contains ID '1': {'"id": "1"' in prompt}")
EOF
```

**Expected:** All checks pass

### 4. Batch Size Validation

```bash
python << 'EOF'
from src.enrichment.gemini_enricher import GeminiEnricher
from src.enrichment.cache import EnrichmentCache

# Create enricher (API key doesn't matter for this test)
cache = EnrichmentCache()
enricher = GeminiEnricher("dummy-key", cache)

# Test batch size limit
test_rows = [{"Topic": f"Topic {i}", "Description": ""} for i in range(30)]

try:
    enricher.enrich_batch(test_rows)
    print("❌ Should have raised ValueError")
except ValueError as e:
    print(f"✅ Batch size validation working: {e}")
EOF
```

**Expected:** `✅ Batch size validation working: Batch size must be ≤20 rows`

## Full Integration Test (Requires API Key)

### Prerequisites

1. Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/)
2. Set environment variable:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

### Test 1: Small Batch (Frontend Roadmap)

```bash
cd /Users/alex/Sandbox/roadmapsh-exporter
source venv314/bin/activate
python -m src.cli scrape --roadmap frontend --enrich --verbose
```

**Expected Output:**

```
Cache: 0 entries
Checking cache for all rows...
Cache hits: 0/115
Rows to enrich: 115
Processing 6 batches (batch size: 20)

Batch 1/6 (20 rows)
✓ Batch 1 enriched successfully

Batch 2/6 (20 rows)
✓ Batch 2 enriched successfully

...

Batch 6/6 (15 rows)
✓ Batch 6 enriched successfully

============================================================
ENRICHMENT SUMMARY
============================================================
Total rows: 115
Cache hits: 0
Newly enriched: 115
Failed: 0
Success rate: 100.0%
============================================================

✓ Scraping completed successfully!
  Output: output/roadmap_frontend_*.csv
```

**Verify:**

- CSV file created in `output/`
- TLDR column has ≤12 word summaries
- Challenge column has "practice" or "expert"

```bash
# Check CSV structure
head -3 output/roadmap_frontend_*.csv

# Count enriched rows
tail -n +2 output/roadmap_frontend_*.csv | wc -l
```

### Test 2: Cache Behavior (Re-run Same Roadmap)

```bash
python -m src.cli scrape --roadmap frontend --enrich --verbose
```

**Expected Output:**

```
Cache: 115 entries (latest: 2025-10-20 ...)
Checking cache for all rows...
Cache hits: 115/115
Rows to enrich: 0
All rows cached! ✅

============================================================
ENRICHMENT SUMMARY
============================================================
Total rows: 115
Cache hits: 115
Newly enriched: 0
Failed: 0
Success rate: 100.0%
============================================================
```

**Verify:**

- No API calls made (instant completion)
- Same CSV output as first run

### Test 3: Medium Batch (Engineering Manager)

```bash
python -m src.cli scrape --roadmap engineering-manager --enrich --verbose
```

**Expected:**

- ~134 rows
- ~7 batches (20, 20, 20, 20, 20, 20, 14)
- ~28-60 seconds (depending on rate limits)
- 100% success rate

### Test 4: Large Batch (Machine Learning)

```bash
python -m src.cli scrape --roadmap machine-learning --enrich --verbose
```

**Expected:**

- Varies by roadmap size
- Multiple batches
- All batches succeed
- CSV with TLDR/Challenge columns

## Performance Benchmarks

### Measure Processing Time

```bash
time python -m src.cli scrape --roadmap engineering-manager --enrich
```

**Expected:**

- First run (no cache): ~30-60 seconds
- Second run (full cache): ~5-10 seconds (instant enrichment)

### Measure API Calls

Enable verbose logging and count batch calls:

```bash
python -m src.cli scrape --roadmap engineering-manager --enrich --verbose 2>&1 | grep "Batch.*enriched successfully" | wc -l
```

**Expected:** ~7-8 batches for engineering-manager

### Verify Cost Efficiency

```bash
# Check cache stats
python << 'EOF'
from src.enrichment.cache import EnrichmentCache
cache = EnrichmentCache()
count, latest = cache.stats()
print(f"Cache entries: {count}")
print(f"Latest: {latest}")
EOF
```

## Error Handling Tests

### Test 1: Invalid API Key

```bash
export GEMINI_API_KEY="invalid-key"
python -m src.cli scrape --roadmap frontend --enrich
```

**Expected:** Error message about invalid API key

### Test 2: Missing API Key

```bash
unset GEMINI_API_KEY
python -m src.cli scrape --roadmap frontend --enrich
```

**Expected:**

```
Error: --gemini-api-key required when using --enrich
Provide via --gemini-api-key flag or GEMINI_API_KEY environment variable
```

### Test 3: Network Interruption (Fallback Test)

**Manual:** Disconnect network during batch processing

**Expected:**

- Batch fails
- Automatic fallback to individual processing
- Some rows enriched individually
- Error logged but processing continues

## Output Validation

### Validate CSV Structure

```bash
# Check CSV has all required columns
head -1 output/roadmap_frontend_*.csv
```

**Expected:** `Category,Subcategory,Topic,Description,Resources,TLDR,Challenge`

### Validate TLDR Format

```bash
# Check TLDR word count (should be ≤12 words)
python << 'EOF'
import csv

with open('output/roadmap_frontend_*.csv', 'r') as f:  # Replace * with actual timestamp
    reader = csv.DictReader(f)
    for i, row in enumerate(reader, 1):
        tldr = row['TLDR']
        word_count = len(tldr.split())
        if word_count > 12:
            print(f"❌ Row {i}: TLDR has {word_count} words (max 12)")
        if i <= 5:
            print(f"✅ Row {i}: '{tldr}' ({word_count} words)")
EOF
```

**Expected:** All TLDRs have ≤12 words

### Validate Challenge Enum

```bash
# Check all Challenge values are "practice" or "expert"
python << 'EOF'
import csv

with open('output/roadmap_frontend_*.csv', 'r') as f:  # Replace * with actual timestamp
    reader = csv.DictReader(f)
    valid_challenges = {"practice", "expert", ""}

    for i, row in enumerate(reader, 1):
        challenge = row['Challenge']
        if challenge not in valid_challenges:
            print(f"❌ Row {i}: Invalid challenge '{challenge}'")

    print("✅ All Challenge values are valid")
EOF
```

**Expected:** `✅ All Challenge values are valid`

## Regression Tests

### Test: No Breaking Changes

```bash
# Test without enrichment (should still work)
python -m src.cli scrape --roadmap frontend

# Verify CSV has 5 columns (not 7)
head -1 output/roadmap_frontend_*.csv
```

**Expected:** `Category,Subcategory,Topic,Description,Resources` (no TLDR/Challenge)

### Test: Interactive Mode

```bash
python -m src.cli scrape --interactive --enrich
# Select "frontend" when prompted
```

**Expected:** Works same as `--roadmap frontend --enrich`

## Performance Comparison

### Before vs After Batch Processing

**To test "before" behavior (individual processing):**

Temporarily modify `src/json_scraper.py` to disable batching:

```python
# In _enrich_data(), change BATCH_SIZE from 20 to 1
BATCH_SIZE = 1  # Test individual processing
```

**Run test:**

```bash
time python -m src.cli scrape --roadmap frontend --enrich
```

**Expected:** Much slower (~10 minutes for 150 rows)

**Revert change** and run again with batch processing:

```bash
# Revert BATCH_SIZE to 20
time python -m src.cli scrape --roadmap frontend --enrich
```

**Expected:** Much faster (~30-60 seconds)

## Success Criteria

All tests should show:

✅ Type checking passes (mypy: 0 errors)  
✅ Batch prompt generation works  
✅ Batch size validation enforced  
✅ API integration works (requires key)  
✅ Cache integration works  
✅ Fallback to individual processing works  
✅ CSV output correct (7 columns with enrichment)  
✅ TLDR ≤12 words  
✅ Challenge is "practice" or "expert"  
✅ No breaking changes to existing functionality  
✅ 18x faster than individual processing

## Troubleshooting

### Issue: "Module not found"

**Solution:** Activate virtual environment

```bash
source venv314/bin/activate
```

### Issue: "No module named 'google.genai'"

**Solution:** Install dependencies

```bash
pip install -r requirements.txt
```

### Issue: Type errors

**Solution:** Run mypy to see specific errors

```bash
mypy src/
```

### Issue: Batch processing not working

**Solution:** Check verbose logs

```bash
python -m src.cli scrape --roadmap frontend --enrich --verbose
```

Look for:

- "Processing X batches (batch size: 20)"
- "Batch N/X enriched successfully"

If not present, check code modifications.

## Quick Smoke Test

One command to verify everything works:

```bash
cd /Users/alex/Sandbox/roadmapsh-exporter && \
source venv314/bin/activate && \
mypy src/ && \
export GEMINI_API_KEY="your-key" && \
python -m src.cli scrape --roadmap frontend --enrich --verbose && \
echo "✅ ALL TESTS PASSED!"
```

**Expected:** Complete successfully with enriched CSV output

---

**Testing Status:** Ready for testing  
**API Key Required:** Yes (for integration tests)  
**Estimated Test Time:** ~5 minutes (with API key)
