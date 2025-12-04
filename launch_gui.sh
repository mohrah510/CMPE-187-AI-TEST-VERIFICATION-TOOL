#!/bin/bash
# Launch the GUI version (Web-based)

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Prevent Python from creating cache files
export PYTHONDONTWRITEBYTECODE=1

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing Flask..."
    pip install flask > /dev/null 2>&1
fi

# Kill any existing processes
echo "Cleaning up any existing processes..."
pkill -f "python.*gui_web" 2>/dev/null
sleep 1

# Check for existing processes on port 5000
if lsof -ti:5000 > /dev/null 2>&1; then
    echo "Warning: Port 5000 is in use. The server will find a free port automatically."
    echo ""
fi

# Launch Web GUI
echo "Starting web server..."
echo "The browser should open automatically."
echo "If it doesn't, look for the URL in the output below."
echo ""
echo "If you see a 403 error, try:"
echo "  1. Clear your browser cache (Cmd+Shift+R on Mac)"
echo "  2. Use incognito/private mode"
echo "  3. Try a different browser"
echo ""
python3 "$SCRIPT_DIR/src/gui_web.py"

# Deactivate virtual environment
deactivate

