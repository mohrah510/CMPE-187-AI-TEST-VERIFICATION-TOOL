#!/bin/bash
# Simple script to run the AI Test Verification Tool with virtual environment

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Prevent Python from creating cache files
export PYTHONDONTWRITEBYTECODE=1

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Run the main script
python3 "$SCRIPT_DIR/src/main.py"

# Deactivate virtual environment
deactivate
