#!/bin/bash
# Quick cleanup script - removes all Python cache files
find . -type d -name "__pycache__" ! -path "./venv/*" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" ! -path "./venv/*" -delete 2>/dev/null
find . -type f -name "*.pyo" ! -path "./venv/*" -delete 2>/dev/null
echo "✓ Cleaned cache files"
