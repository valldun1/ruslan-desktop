#!/usr/bin/env bash
#===============================================================================
# build_dmg.sh — Build Руслан.app and .dmg installer for macOS
#
# Prerequisites:
#   - PyInstaller installed (pip install pyinstaller)
#   - Python venv with all dependencies active
#
# Usage:
#   ./scripts/build_dmg.sh          # build .app only
#   ./scripts/build_dmg.sh --dmg    # build .app + .dmg
#   ./scripts/build_dmg.sh --clean  # clean build artifacts
#===============================================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

APP_NAME="Руслан"
APP_BUNDLE="dist/${APP_NAME}.app"
DMG_NAME="${APP_NAME}.dmg"
DMG_PATH="dist/${DMG_NAME}"
BUILD_DIR=""
ICON_SOURCE="assets/app_icon.icns"

# ── Colors ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'  # No Color

info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ── Helpers ──────────────────────────────────────────────────────────────────
clean_build() {
    info "Cleaning build artifacts …"
    rm -rf build/ dist/ *.spec
    ok "Cleaned."
    exit 0
}

check_prereqs() {
    if ! command -v pyinstaller &>/dev/null; then
        err "PyInstaller not found. Install: pip install pyinstaller"
        exit 1
    fi
    if [[ ! -f "$ICON_SOURCE" ]]; then
        warn "Icon not found at $ICON_SOURCE — .app will use default icon."
    fi
    if ! command -v hdiutil &>/dev/null; then
        err "hdiutil not found — are you on macOS?"
        exit 1
    fi
}

# ── Step 1: PyInstaller ──────────────────────────────────────────────────────
build_app() {
    info "Building ${APP_NAME}.app with PyInstaller …"

    pyinstaller --noconfirm \
        --clean \
        --windowed \
        --name "$APP_NAME" \
        --icon "$ICON_SOURCE" \
        --add-data "assets:assets" \
        --add-data "config:config" \
        --add-data "plugins/*/manifest.json:plugins" \
        --hidden-import core \
        --hidden-import actions \
        --hidden-import actions.engine \
        --hidden-import api \
        --hidden-import api.main \
        --hidden-import brain \
        --hidden-import brain.gateway \
        --hidden-import voice \
        --hidden-import voice.engine \
        --hidden-import ui \
        --hidden-import ui.overlay \
        --hidden-import ui.chat_dialog \
        --hidden-import ui.hotkey \
        --hidden-import ui.drag_drop \
        --hidden-import ui.sprite_widget \
        --hidden-import macos \
        --hidden-import macos.controller \
        --hidden-import memory \
        --hidden-import memory.store \
        --hidden-import plugins \
        --hidden-import plugins.manager \
        --hidden-import pydantic \
        --hidden-import pydantic_settings \
        --hidden-import loguru \
        --hidden-import anyio \
        --hidden-import httpx \
        core/main.py

    ok "App bundle created: ${APP_BUNDLE}"
}

# ── Step 2: DMG ──────────────────────────────────────────────────────────────
build_dmg() {
    local dmg_tmp dist_dir temp_dir app_name_stripped volume_name
    dmg_tmp="$(mktemp -d)"
    dist_dir="$(dirname "$APP_BUNDLE")"
    temp_dir="${dmg_tmp}/dmg"
    app_name_stripped="${APP_NAME}"  # keep Unicode name

    info "Creating DMG …"

    mkdir -p "$temp_dir"

    # Copy .app into DMG staging
    cp -R "$APP_BUNDLE" "$temp_dir/"

    # Create Applications shortcut
    ln -s /Applications "$temp_dir/Applications"

    volume_name="Руслан Desktop Agent"
    local dmg_staging
    dmg_staging="${dmg_tmp}/${DMG_NAME}"

    # Build read-write DMG first
    hdiutil create \
        -srcfolder "$temp_dir" \
        -volname "$volume_name" \
        -fs HFS+ \
        -format UDRW \
        -ov \
        "$dmg_staging" 2>/dev/null

    # Mount, configure window position, then unmount
    local mount_point device
    mount_point="/Volumes/${volume_name}"
    device="$(hdiutil attach -nobrowse -readwrite "$dmg_staging" 2>/dev/null | tail -1 | awk '{print $1}')"

    if [[ -d "$mount_point" ]]; then
        # Set icon position via AppleScript
        osascript <<-EOS 2>/dev/null || true
            tell application "Finder"
                tell disk "${volume_name}"
                    open
                    set current view of container window to icon view
                    set toolbar visible of container window to false
                    set statusbar visible of container window to false
                    -- Window size
                    set bounds of container window to {400, 200, 900, 500}
                    -- Icon positions
                    set position of item "${APP_NAME}.app" of container window to {130, 180}
                    set position of item "Applications" of container window to {380, 180}
                    -- Icon size
                    set icon size of the icon view options of container window to 96
                    -- Text size
                    set text size of the icon view options of container window to 12
                    close
                end tell
            end tell
EOS

        # Wait a moment for Finder
        sleep 2

        # Set custom volume icon (if app_icon.icns exists, use it as volume icon)
        if [[ -f "$ICON_SOURCE" ]]; then
            # Convert icns to icns for volume icon
            cp "$ICON_SOURCE" "$mount_point/.VolumeIcon.icns" 2>/dev/null || true
            # Set the custom icon attribute
            SetFile -a C "$mount_point" 2>/dev/null || true
        fi

        # Detach
        hdiutil detach "$device" -quiet 2>/dev/null || true
    fi

    # Convert to compressed read-only DMG
    rm -f "$DMG_PATH"
    hdiutil convert \
        "$dmg_staging" \
        -format UDZO \
        -imagekey zlib-level=9 \
        -o "$DMG_PATH" 2>/dev/null

    # Cleanup temp
    rm -rf "$dmg_tmp"

    if [[ -f "$DMG_PATH" ]]; then
        local size
        size="$(du -h "$DMG_PATH" | cut -f1)"
        ok "DMG created: ${DMG_PATH} (${size})"
    else
        err "DMG creation failed."
        exit 1
    fi
}

# ── Main ─────────────────────────────────────────────────────────────────────
main() {
    local do_dmg=false
    for arg in "$@"; do
        case "$arg" in
            --clean) clean_build ;;
            --dmg)   do_dmg=true ;;
            --help|-h)
                echo "Usage: $0 [--dmg] [--clean] [--help]"
                echo ""
                echo "  --dmg    Build .app + compressed .dmg"
                echo "  --clean  Remove build/ dist/ artifacts"
                exit 0
                ;;
        esac
    done

    check_prereqs
    build_app

    if $do_dmg; then
        build_dmg
    else
        ok "Done. App bundle: ${APP_BUNDLE}"
        echo ""
        echo "  To also create a .dmg installer, run:"
        echo "    $0 --dmg"
    fi
}

main "$@"
