# Changelog

All notable changes to **Ghalam** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Every released version
corresponds to a `vX.Y.Z` git tag.

---

## [0.3.2] - 2026-10-23

Desktop icon fixes so Ghalam shows up properly in taskbars, docks and app menus.

### Added

- `assets/icons/` with 16, 24, 32, 48, 64, 128, 256 and 512 px icons, generated from
  `assets/icon.png` by `scripts/generate_icons.py`.

### Changed

- The application builds one multi-size `QIcon` and shares it between the window and the tray,
  instead of handing a single 512 px file to both.
- The drawn fallback icon is now device-pixel-ratio aware.
- The desktop file name honours `FLATPAK_ID` when the app runs inside a Flatpak sandbox.

### Fixed

- The X11 window icon was empty because only one oversized icon was supplied; the set now starts
  at 128 px, which is the size the backend exports into `_NET_WM_ICON`.
- `ghalam.desktop` now carries `StartupWMClass=Ghalam`, so the window associates with the launcher
  instead of showing a generic icon.
- `install.sh`, `setup.sh` and `aur/PKGBUILD` install the full icon set into `hicolor`, no longer
  leave a stray PNG at the theme root, and no longer refresh an icon cache directory that has no
  `index.theme`.
- Uninstalling removes every installed icon size, the legacy stray copy and any stale cache file.

---

## [0.3.1] - 2026-10-23

Documentation-only release: the project now keeps a changelog.

### Documentation

- Added `CHANGELOG.md`, covering 0.1.0, 0.2.0 and 0.3.0 in Keep a Changelog format with compare
  links, so every tag has a written record of what changed.

---

## [0.3.0] - 2026-10-23

Bundled Persian typography, shipped offline.

### Added

- **Bundled Vazirmatn font family** (`assets/fonts/`): Regular, Medium, SemiBold and Bold, with the
  SIL OFL 1.1 license. Persian and Latin annotations render correctly without installing any system
  font, and the app stays fully offline.
- **`ghalam/fonts.py`** - `load_fonts()` registers the bundled faces through `QFontDatabase` and is
  idempotent. It raises a clear `RuntimeError` when called before a `QGuiApplication` exists, instead
  of crashing the process.
- **Typography constants** in `config.py`: `FONT_FAMILY`, `FONT_WEIGHTS`, `UI_FONT_STACK` and
  `MONO_FONT_STACK`, so the family name and fallback stacks have a single source of truth.
- **Application-wide default font**: Vazirmatn is registered and applied right after the
  `QApplication` is created, before any widget exists.

### Changed

- The inline text tool, `TextItem`, `BadgeItem` and the toolbar card now render with the bundled
  family instead of the generic `Sans Serif` fallback.
- The toolbar stylesheet derives its UI and mono stacks from the config constants rather than
  re-inlining them.
- The wheel force-includes `assets/` and the sdist declares an explicit include/exclude list, so a
  plain `pip install ghalam` and the PyInstaller bundle both find icons and fonts.
- Missing or rejected font files are now logged as warnings and retried on the next call, instead of
  being silently latched as loaded.

### Removed

- The unused `fonts.make_font()` helper.

### Documentation

- Added an offline-typography feature bullet to `README.md` and `README_FA.md`.

### Tooling

- The local `tmp/` scratch directory is excluded from ruff and from the sdist.

---

## [0.2.0] - 2026-10-08

GNOME compatibility, a friendlier default shortcut, and safer text input.

### Added

- `Alt+D` as the default global shortcut, with GNOME keybinding support alongside KDE.

### Fixed

- Transparency on GNOME/Mutter Wayland: the overlay is shown with its exact screen geometry instead
  of `showFullScreen()`, which disabled compositor alpha blending and rendered a black overlay.
- Typing in the inline text editor no longer triggers tool shortcuts, and the toolbar toggle is
  restricted to `Tab`.
- Desktop filename suffix corrected to `ghalam`.

---

## [0.1.0] - 2026-10-08

First public release.

### Added

- Fullscreen transparent overlay with a quick toggle, for KDE Plasma/Wayland, X11 and GNOME.
- Floating glassmorphic toolbar with a curated palette, an interactive custom colour picker, and
  live stroke-width control.
- Drawing primitives: pen, highlighter, arrow, rectangle, ellipse, text and numbered badges, with
  undo/redo and clear.
- Composite screenshot capture with clipboard copy (`Ctrl+C`) and save (`Ctrl+S`).
- Single-instance IPC daemon with a CLI (`--daemon`, `--toggle`, `--quit`, `--monitor`) and a
  system-tray icon.
- Multi-monitor support, including KWin DBus active-output detection.
- PyInstaller single-file build, `uv`-based launcher, desktop entry, and a one-line `curl` installer.
- Arch User Repository packaging (`aur/PKGBUILD`).
- GitHub Actions workflows for CI and tag-driven releases.
- English and Persian documentation.

---

[0.3.2]: https://github.com/mryazdan/ghalam/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/mryazdan/ghalam/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/mryazdan/ghalam/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/mryazdan/ghalam/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/mryazdan/ghalam/releases/tag/v0.1.0
