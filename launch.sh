#!/bin/bash
# Launch the interactive menu

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Prevent Python from creating cache files
export PYTHONDONTWRITEBYTECODE=1

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Launch interactive menu
python3 "$SCRIPT_DIR/src/menu.py"

# Deactivate virtual environment
deactivate
