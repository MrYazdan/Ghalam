#!/usr/bin/env bash
# ==============================================================================
# Ghalam (قلم) - Universal Linux Installer
# Fast, elegant screen drawing & annotation tool for Linux
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/mryazdan/ghalam/main/install.sh | bash
# Or with options:
#   bash install.sh [--uninstall] [--shortcut "Meta+Shift+A"]
# ==============================================================================

set -e

REPO="mryazdan/ghalam"
BINARY_NAME="ghalam-linux-x86_64"
TARGET_NAME="ghalam"
DEFAULT_SHORTCUT="Alt+D"
SHORTCUT="$DEFAULT_SHORTCUT"
UNINSTALL=false

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

# ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

# Parse optional arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --uninstall|-u)
            UNINSTALL=true
            shift
            ;;
        --shortcut|-s)
            SHORTCUT="$2"
            shift 2
            ;;
        --help|-h)
            echo "Ghalam (قلم) Installer"
            echo "Usage: install.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -s, --shortcut <KEYS>   Set global shortcut (default: Alt+D)"
            echo "  -u, --uninstall         Uninstall Ghalam and all associated files"
            echo "  -h, --help              Show this help message"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

BIN_DIR="${HOME}/.local/bin"
APP_DIR="${HOME}/.local/share/applications"
ICON_DIR="${HOME}/.local/share/icons"

print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "  ╔═══════════════════════════════════════════════════╗"
    echo "  ║                Ghalam (قلم) Installer             ║"
    echo "  ║   Fast, elegant screen drawing & annotation tool  ║"
    echo "  ╚═══════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

do_uninstall() {
    print_header
    echo -e "${YELLOW}Uninstalling Ghalam...${NC}"

    rm -f "${BIN_DIR}/${TARGET_NAME}"
    rm -f "${APP_DIR}/ghalam.desktop"
    rm -f "${ICON_DIR}/ghalam.png"
    rm -f "${ICON_DIR}/hicolor/512x512/apps/ghalam.png"
    rm -f "${ICON_DIR}/hicolor/scalable/apps/ghalam.svg"

    if command -v kwriteconfig6 &>/dev/null; then
        kwriteconfig6 --file kglobalshortcutsrc --group services --group ghalam.desktop --delete 2>/dev/null || true
    elif command -v kwriteconfig5 &>/dev/null; then
        kwriteconfig5 --file kglobalshortcutsrc --group services --group ghalam.desktop --delete 2>/dev/null || true
    fi

    if command -v gsettings &>/dev/null; then
        local SCHEMA="org.gnome.settings-daemon.plugins.media-keys"
        local KEY_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/ghalam/"
        local CURRENT_LIST="$(gsettings get $SCHEMA custom-keybindings 2>/dev/null || echo "[]")"
        if [[ "$CURRENT_LIST" == *"$KEY_PATH"* ]]; then
            local CLEANED_LIST=$(echo "$CURRENT_LIST" | sed "s|'$KEY_PATH',*||g" | sed "s|, *]$|]|" | sed "s|\[, *|[|")
            [ "$CLEANED_LIST" = "[]" ] && CLEANED_LIST="@as []"
            gsettings set $SCHEMA custom-keybindings "$CLEANED_LIST" 2>/dev/null || true
        fi
        gsettings reset-recursively "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${KEY_PATH}" 2>/dev/null || true
    fi

    update-desktop-database "${APP_DIR}" 2>/dev/null || true
    gtk-update-icon-cache -q -t "${ICON_DIR}" 2>/dev/null || true

    echo -e "${GREEN}✓ Ghalam has been completely removed from your system.${NC}"
    exit 0
}

if [ "$UNINSTALL" = true ]; then
    do_uninstall
fi

print_header

# 1. System checks
OS="$(uname -s)"
ARCH="$(uname -m)"

if [ "$OS" != "Linux" ]; then
    echo -e "${RED}Error: Ghalam is currently only supported on Linux (detected: $OS).${NC}"
    exit 1
fi

if [ "$ARCH" != "x86_64" ]; then
    echo -e "${RED}Error: Prebuilt binary is only available for x86_64 (detected: $ARCH).${NC}"
    echo -e "You can still run Ghalam from source with Python and PyQt6."
    exit 1
fi

# Determine download tool
if command -v curl &>/dev/null; then
    DOWNLOAD_CMD="curl -fL --progress-bar -o"
elif command -v wget &>/dev/null; then
    DOWNLOAD_CMD="wget -q --show-progress -O"
else
    echo -e "${RED}Error: 'curl' or 'wget' is required to download Ghalam.${NC}"
    exit 1
fi

# Prepare directories
mkdir -p "${BIN_DIR}"
mkdir -p "${APP_DIR}"
mkdir -p "${ICON_DIR}/hicolor/512x512/apps"
mkdir -p "${ICON_DIR}/hicolor/scalable/apps"

# 2. Download standalone binary
RELEASE_URL="https://github.com/${REPO}/releases/latest/download/${BINARY_NAME}"
TEMP_BIN="$(mktemp "${BIN_DIR}/ghalam.tmp.XXXXXX")"

echo -e "${BLUE}▶ Downloading standalone binary from GitHub Releases...${NC}"
if ! $DOWNLOAD_CMD "${TEMP_BIN}" "${RELEASE_URL}"; then
    rm -f "${TEMP_BIN}"
    echo -e "${YELLOW}Could not download latest release binary.${NC}"
    echo -e "${YELLOW}Falling back to checking local build or repository...${NC}"

    # Check if run locally within repo where dist/ exists
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo "")"
    if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/dist/${BINARY_NAME}" ]; then
        echo -e "${GREEN}✓ Found local build in dist/${BINARY_NAME}! Using local build.${NC}"
        cp "$SCRIPT_DIR/dist/${BINARY_NAME}" "${BIN_DIR}/${TARGET_NAME}"
    else
        echo -e "${RED}Download failed. Please check your internet connection or verify release at:${NC}"
        echo -e "  https://github.com/${REPO}/releases"
        exit 1
    fi
else
    mv -f "${TEMP_BIN}" "${BIN_DIR}/${TARGET_NAME}"
fi

chmod +x "${BIN_DIR}/${TARGET_NAME}"
echo -e "${GREEN}✓ Installed executable: ${BIN_DIR}/${TARGET_NAME}${NC}"

# 3. Install icons
RAW_BASE="https://raw.githubusercontent.com/${REPO}/main"
echo -e "${BLUE}▶ Installing application icons...${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo "")"
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/assets/icon.png" ]; then
    cp "$SCRIPT_DIR/assets/icon.png" "${ICON_DIR}/ghalam.png"
    cp "$SCRIPT_DIR/assets/icon.png" "${ICON_DIR}/hicolor/512x512/apps/ghalam.png"
    cp "$SCRIPT_DIR/assets/icon.svg" "${ICON_DIR}/hicolor/scalable/apps/ghalam.svg"
else
    $DOWNLOAD_CMD "${ICON_DIR}/ghalam.png" "${RAW_BASE}/assets/icon.png" 2>/dev/null || true
    cp "${ICON_DIR}/ghalam.png" "${ICON_DIR}/hicolor/512x512/apps/ghalam.png" 2>/dev/null || true
    $DOWNLOAD_CMD "${ICON_DIR}/hicolor/scalable/apps/ghalam.svg" "${RAW_BASE}/assets/icon.svg" 2>/dev/null || true
fi
echo -e "${GREEN}✓ Application icons installed.${NC}"

# 4. Install Desktop Entry
echo -e "${BLUE}▶ Creating desktop launcher...${NC}"
cat <<EOF > "${APP_DIR}/ghalam.desktop"
[Desktop Entry]
Name=Ghalam
GenericName=Screen Annotator
Comment=Ghalam (قلم) - Fast, elegant screen drawing & annotation tool
Exec=${BIN_DIR}/${TARGET_NAME}
Icon=ghalam
Terminal=false
Type=Application
Categories=Utility;Graphics;
Keywords=ghalam;pen;screen;annotate;draw;highlighter;screenshot;
StartupNotify=false
EOF

update-desktop-database "${APP_DIR}" 2>/dev/null || true
gtk-update-icon-cache -q -t "${ICON_DIR}" 2>/dev/null || true
echo -e "${GREEN}✓ Desktop launcher installed: ${APP_DIR}/ghalam.desktop${NC}"

# 5. Configure Shortcut (KDE Plasma & GNOME)
echo -e "${BLUE}▶ Configuring global shortcut...${NC}"
CONFIGURED_SHORTCUT=false

if command -v kwriteconfig6 &>/dev/null; then
    kwriteconfig6 --file kglobalshortcutsrc --group services --group screen-annotator.desktop --delete 2>/dev/null || true
    kwriteconfig6 --file kglobalshortcutsrc --group services --group ghalam.desktop --key _launch --notify "$SHORTCUT"
    echo -e "${GREEN}✓ Registered global shortcut: [${SHORTCUT}] in KDE Plasma 6${NC}"
    CONFIGURED_SHORTCUT=true
elif command -v kwriteconfig5 &>/dev/null; then
    kwriteconfig5 --file kglobalshortcutsrc --group services --group screen-annotator.desktop --delete 2>/dev/null || true
    kwriteconfig5 --file kglobalshortcutsrc --group services --group ghalam.desktop --key _launch "$SHORTCUT"
    echo -e "${GREEN}✓ Registered global shortcut: [${SHORTCUT}] in KDE Plasma 5${NC}"
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
        gsettings set "$BINDING_SCHEMA" command "${BIN_DIR}/${TARGET_NAME}" 2>/dev/null || true
        gsettings set "$BINDING_SCHEMA" binding "$GNOME_SHORTCUT" 2>/dev/null || true
        echo -e "${GREEN}✓ Registered global shortcut: [${SHORTCUT}] (${GNOME_SHORTCUT}) in GNOME Desktop${NC}"
        CONFIGURED_SHORTCUT=true
    fi
fi

if [ "$CONFIGURED_SHORTCUT" = false ]; then
    echo -e "${YELLOW}ℹ Non-KDE/GNOME desktop detected. To bind a shortcut in your desktop environment:${NC}"
    echo -e "  Command: ${BOLD}${BIN_DIR}/${TARGET_NAME}${NC}"
    echo -e "  Suggested Shortcut: ${BOLD}${SHORTCUT}${NC}"
fi

# 6. Check PATH
PATH_WARNING=""
case ":$PATH:" in
    *":${BIN_DIR}:"*) ;;
    *)
        PATH_WARNING=true
        echo ""
        echo -e "${YELLOW}⚠ Note: ${BIN_DIR} is not currently in your PATH.${NC}"
        echo -e "  Add it to your shell config (~/.bashrc or ~/.zshrc):"
        echo -e "    ${BOLD}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
        ;;
esac

echo ""
echo -e "${GREEN}${BOLD}═════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}             🎉 Ghalam installed successfully!             ${NC}"
echo -e "${GREEN}${BOLD}═════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Launch Ghalam anytime by:"
echo -e "  1. Global Shortcut:   ${CYAN}${BOLD}${SHORTCUT}${NC}"
echo -e "  2. Terminal:          ${CYAN}${BOLD}ghalam${NC} (or ${BIN_DIR}/ghalam)"
echo -e "  3. Application Menu:  Search for ${CYAN}${BOLD}Ghalam${NC}"
echo ""
echo -e "To uninstall:"
echo -e "  ${CYAN}curl -fsSL https://raw.githubusercontent.com/${REPO}/main/install.sh | bash -s -- --uninstall${NC}"
echo ""
