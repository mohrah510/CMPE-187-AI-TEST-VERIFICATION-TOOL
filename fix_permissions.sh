#!/bin/bash
# Fix permissions for the AI Test Verification Tool

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Fixing permissions for AI Test Verification Tool..."
echo ""

# Create directories with proper permissions
mkdir -p "$SCRIPT_DIR/uploads"
mkdir -p "$SCRIPT_DIR/output"

# Set directory permissions
chmod 755 "$SCRIPT_DIR/uploads"
chmod 755 "$SCRIPT_DIR/output"

# Set file permissions for Python scripts
find "$SCRIPT_DIR/src" -name "*.py" -type f -exec chmod 644 {} \;

# Make scripts executable
chmod +x "$SCRIPT_DIR/launch_gui.sh"
chmod +x "$SCRIPT_DIR/launch.sh"
chmod +x "$SCRIPT_DIR/run.sh" 2>/dev/null || true

echo "✓ Permissions fixed!"
echo ""
echo "Directories:"
ls -ld "$SCRIPT_DIR/uploads" "$SCRIPT_DIR/output"
echo ""
echo "You can now run: ./launch_gui.sh"

