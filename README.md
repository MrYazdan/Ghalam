<p align="center">
  <img src="assets/icon.png" width="128" height="128" alt="Ghalam Icon" />
</p>

<p align="center">
  <b>Fast, minimalist, elegant screen drawing & annotation tool for Linux</b>
  <br />
  <i>Lightweight • Glassmorphic UI • Instant Dismiss • Multi-Monitor Ready • Powered by uv</i>
</p>

<p align="center">
  <a href="README.md"><b>English</b></a> |
  <a href="README_FA.md"><b>فارسی</b></a>
</p>

**Ghalam** (Persian for *"Pen"* / *قلم*) is a modern, lightweight on-screen annotation utility designed for Linux
desktops (optimized for KDE Plasma & Wayland, X11, and cross-platform).

Triggered instantly with a global keyboard shortcut, it displays a transparent, distraction-free canvas over your
screen. You can sketch ideas, highlight text, draw precision arrows, annotate bugs, or stamp step-by-step badges.
Pressing **`Esc`** clears everything instantly and terminates the process cleanly without leftover background jobs.

## Key Features

- **Full Drawing Suite**:
    - **Freehand Pen**: Anti-aliased, smooth quadratic Bézier interpolation.
    - **Highlighter**: Translucent fluorescent marker for emphasizing text and UI elements.
    - **Smart Arrow**: Directional arrows with calculated geometric heads.
    - **Shapes**: Rounded rectangles and circles/ellipses.
    - **Step Counter Badges (①, ②, ③...)**: Automatically incrementing numbered pins for documentation and bug
      reproduction steps.
    - **Inline Text Tool**: Click anywhere to type notes and labels with high-contrast backing.
- **Distraction-Free & Floating Glassmorphic Toolbar**:
    - **Hidden by default**: Starts completely clean so you can sketch immediately.
    - **Instant toggle with `Tab` or `Space`**: Pops in a floating Obsidian dark glass card with drop shadow, visible
      and crisp across both pure white documents and dark themes.
    - Draggable anywhere across monitors.
    - Quick cycle stroke size button and mouse scroll wheel resizing.
- **Multi-Monitor & Fractional Scale Support**:
    - Automatically identifies the active display via KWin DBus.
    - Supports heterogeneous scaling (e.g. 100% on DisplayPort + 75% on HDMI).
    - Quick monitor hopping with **`M`** or span all monitors simultaneously with `--monitor all`.
- **Clean Termination**:
    - Pressing **`Esc`** or the **`✕`** button cleans up memory and immediately terminates the process.
    - Full `Ctrl+C` (SIGINT) support in terminal.
- **One-Click Share**:
    - **`Ctrl + C`**: Copies the composite screenshot with your annotations directly to the system clipboard.
    - **`Ctrl + S`**: Saves the screenshot to `~/Pictures/Screenshots`.
- **Powered by `uv`**:
    - Zero dependency setup friction; sub-millisecond start time with lockfile precision (`uv.lock`).

## Keyboard Shortcuts

| Shortcut                                 | Description                                                                |
|------------------------------------------|----------------------------------------------------------------------------|
| :                                        | :                                                                          |
| **`Esc`** or **`✕`**                     | **Instantly dismiss, clear all annotations, and quit**                     |
| **`Tab`** or **`Space`** or **`V`**      | **Toggle Toolbar panel visibility (Show / Hide)**                          |
| **`P`**                                  | Pen tool (smooth freehand drawing)                                         |
| **`H`**                                  | Highlighter tool (translucent marker)                                      |
| **`A`**                                  | Arrow tool (directional pointer)                                           |
| **`R`**                                  | Rectangle tool (rounded boxes)                                             |
| **`O`**                                  | Circle / Ellipse tool                                                      |
| **`T`**                                  | Text tool (click on canvas to type)                                        |
| **`N`**                                  | Numbered Step Badge (1, 2, 3...)                                           |
| **`1` – `7`**                            | Quick Color Presets (Neon Green, Cyan, Red, Yellow, Orange, Purple, White) |
| **`Mouse Wheel`**                        | Increase / decrease brush stroke width                                     |
| **`M`**                                  | Switch overlay between connected monitors                                  |
| **`Ctrl + Z`**                           | Undo previous action                                                       |
| **`Ctrl + Y`** or **`Ctrl + Shift + Z`** | Redo previous action                                                       |
| **`C`**                                  | Clear all drawings on canvas                                               |
| **`Ctrl + C`**                           | Copy annotated screenshot to clipboard                                     |
| **`Ctrl + S`**                           | Save screenshot to disk (PNG)                                              |

## Getting Started

### 1. Requirements

- Python `>= 3.10`
- [uv](https://github.com/astral-sh/uv) (recommended) or standard `python3-venv`

### 2. Launching Ghalam

#### Arch Linux (AUR)

If you are on Arch Linux, Garuda, Manjaro, or EndeavourOS:

```bash
yay -S ghalam
# or
paru -S ghalam
```

#### Using Portable Launcher

The self-contained `run.sh` script automatically detects `uv` or provisions a local `.venv` inside the project folder:

```bash
./run.sh
```

### 3. Setting Up the Global Shortcut

Run the included setup script to register the global shortcut and application launcher:

```bash
./setup_shortcut.sh
```

* Default global shortcut: **`Meta + Shift + A`** (`Super + Shift + A`).
* You can also specify any custom shortcut:

```bash
./setup_shortcut.sh "F8"
# or
./setup_shortcut.sh "Ctrl+Alt+A"
```

Once installed, you can launch Ghalam from anywhere by:

1. Pressing your shortcut (**`Meta + Shift + A`**)
2. Running `ghalam` in any terminal
3. Searching for **Ghalam** in your desktop application menu

## Multi-Monitor Options

Ghalam automatically detects which monitor you are working on. You can also specify display targets:

```bash
# Annotate simultaneously across all connected monitors:
ghalam --monitor all

# Force specific monitor:
ghalam --monitor hdmi
ghalam --monitor dp
```

## License

Open-source under the [MIT License](LICENSE).
