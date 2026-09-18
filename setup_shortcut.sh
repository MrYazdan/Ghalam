#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_FILE="$PROJECT_DIR/ghalam.desktop"
APP_DIR="$HOME/.local/share/applications"
BIN_DIR="$HOME/.local/bin"
SHORTCUT="${1:-Meta+Shift+A}"

echo "====================================================="
echo "       Ghalam (قلم) - Shortcut & Desktop Setup       "
echo "====================================================="

# 1. Install ghalam.desktop and remove old entries
mkdir -p "$APP_DIR"
rm -f "$APP_DIR/screen-annotator.desktop"
cp "$DESKTOP_FILE" "$APP_DIR/ghalam.desktop"
update-desktop-database "$APP_DIR" 2>/dev/null || true
echo "✓ Installed desktop entry to $APP_DIR/ghalam.desktop"

# 2. Symlink to ~/.local/bin/ghalam for terminal execution anywhere
mkdir -p "$BIN_DIR"
ln -sf "$PROJECT_DIR/run.sh" "$BIN_DIR/ghalam"
echo "✓ Created terminal launcher link: $BIN_DIR/ghalam"

# 3. Configure KDE Global Shortcut
if command -v kwriteconfig6 &>/dev/null; then
    # Clear old entry if present
    kwriteconfig6 --file kglobalshortcutsrc --group services --group screen-annotator.desktop --delete 2>/dev/null || true
    kwriteconfig6 --file kglobalshortcutsrc --group services --group ghalam.desktop --key _launch --notify "$SHORTCUT"
    echo "✓ Registered global shortcut: [$SHORTCUT] in KDE Plasma 6"
elif command -v kwriteconfig5 &>/dev/null; then
    kwriteconfig5 --file kglobalshortcutsrc --group services --group screen-annotator.desktop --delete 2>/dev/null || true
    kwriteconfig5 --file kglobalshortcutsrc --group services --group ghalam.desktop --key _launch "$SHORTCUT"
    echo "✓ Registered global shortcut: [$SHORTCUT] in KDE Plasma 5"
fi

echo ""
echo "Setup complete! You can now launch Ghalam anytime by:"
echo "  1. Pressing [$SHORTCUT]"
echo "  2. Typing 'ghalam' in your terminal"
echo "  3. Searching 'Ghalam' in your desktop application launcher"
