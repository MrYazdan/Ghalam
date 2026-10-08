#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_FILE="$PROJECT_DIR/ghalam.desktop"
APP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons"
BIN_DIR="$HOME/.local/bin"
SHORTCUT="${1:-Alt+D}"

convert_to_gnome_shortcut() {
    local s="$1"
    s=$(echo "$s" | sed -E "s/Meta/Super/g; s/Ctrl/Primary/g")
    IFS="+" read -ra PARTS <<< "$s"
    local result=""
    for p in "${PARTS[@]}"; do
        if [[ "$p" =~ ^(Super|Primary|Alt|Shift)$ ]]; then
            result+="<$p>"
        else
            result+="$(echo "$p" | tr "[:upper:]" "[:lower:]")"
        fi
    done
    echo "$result"
}

echo "====================================================="
echo "            Ghalam (قلم) - System Setup              "
echo "====================================================="

# 1. Install user icons
mkdir -p "$ICON_DIR" "$ICON_DIR/hicolor/512x512/apps" "$ICON_DIR/hicolor/scalable/apps"
cp "$PROJECT_DIR/assets/icon.png" "$ICON_DIR/ghalam.png"
cp "$PROJECT_DIR/assets/icon.png" "$ICON_DIR/hicolor/512x512/apps/ghalam.png"
cp "$PROJECT_DIR/assets/icon.svg" "$ICON_DIR/hicolor/scalable/apps/ghalam.svg"

# 2. Symlink to ~/.local/bin/ghalam for terminal execution anywhere
mkdir -p "$BIN_DIR"
ln -sf "$PROJECT_DIR/run.sh" "$BIN_DIR/ghalam"
echo "✓ Created terminal launcher link: $BIN_DIR/ghalam"

# 3. Install ghalam.desktop (using ~/.local/bin/ghalam for portable execution)
mkdir -p "$APP_DIR"
rm -f "$APP_DIR/screen-annotator.desktop"
sed -e "s|^Exec=.*|Exec=$BIN_DIR/ghalam|" \
    -e "s|^Icon=.*|Icon=ghalam|" \
    "$DESKTOP_FILE" > "$APP_DIR/ghalam.desktop"

update-desktop-database "$APP_DIR" 2>/dev/null || true
gtk-update-icon-cache -q -t "$ICON_DIR" 2>/dev/null || true
echo "✓ Installed desktop entry to $APP_DIR/ghalam.desktop"

# 4. Configure Global Shortcut (KDE Plasma & GNOME)
CONFIGURED_SHORTCUT=false

if command -v kwriteconfig6 &>/dev/null; then
    # Clear old entry if present
    kwriteconfig6 --file kglobalshortcutsrc --group services --group screen-annotator.desktop --delete 2>/dev/null || true
    kwriteconfig6 --file kglobalshortcutsrc --group services --group ghalam.desktop --key _launch --notify "$SHORTCUT"
    echo "✓ Registered global shortcut: [$SHORTCUT] in KDE Plasma 6"
    CONFIGURED_SHORTCUT=true
elif command -v kwriteconfig5 &>/dev/null; then
    kwriteconfig5 --file kglobalshortcutsrc --group services --group screen-annotator.desktop --delete 2>/dev/null || true
    kwriteconfig5 --file kglobalshortcutsrc --group services --group ghalam.desktop --key _launch "$SHORTCUT"
    echo "✓ Registered global shortcut: [$SHORTCUT] in KDE Plasma 5"
    CONFIGURED_SHORTCUT=true
fi

if command -v gsettings &>/dev/null; then
    if gsettings list-schemas 2>/dev/null | grep -q "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"; then
        SCHEMA="org.gnome.settings-daemon.plugins.media-keys"
        KEY_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/ghalam/"
        BINDING_SCHEMA="org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${KEY_PATH}"
        GNOME_SHORTCUT="$(convert_to_gnome_shortcut "$SHORTCUT")"

        CURRENT_LIST="$(gsettings get $SCHEMA custom-keybindings 2>/dev/null || echo "@as []")"
        if [[ "$CURRENT_LIST" != *"$KEY_PATH"* ]]; then
            if [ "$CURRENT_LIST" = "@as []" ] || [ "$CURRENT_LIST" = "[]" ]; then
                NEW_LIST="['$KEY_PATH']"
            else
                NEW_LIST="${CURRENT_LIST%]*}, '$KEY_PATH']"
            fi
            gsettings set $SCHEMA custom-keybindings "$NEW_LIST" 2>/dev/null || true
        fi

        gsettings set "$BINDING_SCHEMA" name 'Ghalam' 2>/dev/null || true
        gsettings set "$BINDING_SCHEMA" command "$BIN_DIR/ghalam" 2>/dev/null || true
        gsettings set "$BINDING_SCHEMA" binding "$GNOME_SHORTCUT" 2>/dev/null || true
        echo "✓ Registered global shortcut: [$SHORTCUT] ($GNOME_SHORTCUT) in GNOME Desktop"
        CONFIGURED_SHORTCUT=true
    fi
fi

echo ""
echo "Setup complete! You can now launch Ghalam anytime by:"
echo "  1. Pressing [$SHORTCUT]"
echo "  2. Typing 'ghalam' in your terminal"
echo "  3. Searching 'Ghalam' in your desktop application launcher"
