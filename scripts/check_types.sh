#!/bin/bash
set -e
echo "Running mypy type checks..."
mypy src/
echo "✅ Type checking passed!"

