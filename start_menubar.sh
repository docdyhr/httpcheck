#!/bin/bash
# Startup script for onSite - HTTP Site Monitor

echo "🚀 Starting onSite..."

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This menu bar app only works on macOS"
    exit 1
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."

python3 -c "import rumps, requests, httpcheck" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Missing dependencies. Installing..."
    pip install rumps requests tqdm tabulate pyobjc

    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

echo "✅ Dependencies OK"

# Create config directory if it doesn't exist
CONFIG_DIR="$HOME/.httpcheck"
if [ ! -d "$CONFIG_DIR" ]; then
    echo "📁 Creating config directory at $CONFIG_DIR"
    mkdir -p "$CONFIG_DIR"
fi

# Create default sites file if it doesn't exist
SITES_FILE="$CONFIG_DIR/sites.json"
if [ ! -f "$SITES_FILE" ]; then
    echo "📝 Creating default sites configuration..."
    cat > "$SITES_FILE" << EOF
{
  "sites": [
    "https://google.com",
    "https://github.com",
    "https://stackoverflow.com"
  ]
}
EOF
    echo "✅ Created default sites: google.com, github.com, stackoverflow.com"
    echo "📅 Default check interval: 15 minutes (900 seconds)"
fi

echo "🎯 Starting onSite menu bar app..."
echo "💡 Look for the ⚡ lightning icon in your menu bar!"
echo "💡 White lightning = all good, Red lightning = failures detected"
echo "💡 Use Ctrl+C to stop the app"
echo ""
echo "✨ Features:"
echo "  - Add sites using AppleScript dialogs (automatically checks status)"
echo "  - Remove sites with native list picker"
echo "  - Quit menu item always available"
echo "  - Rich native notifications with sounds"
echo "  - Default check interval: 15 minutes"
echo "  - Logs stored in ~/Library/Logs/onSite/ (macOS best practice)"
echo ""

# Run the app
python3 httpcheck_menubar.py
