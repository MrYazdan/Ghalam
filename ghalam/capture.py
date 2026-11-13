"""
Desktop capture helpers: tool selection, per-screen crops and command builders.

The module is widget-free. Callers pass ``QRect``/``QSize`` values in, and the
command builders return argv lists, so the geometry and precedence rules are
unit-testable without a compositor.
"""
import logging
import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable

from PyQt6.QtCore import QCoreApplication, QEventLoop, QPoint, QRect, QSize, QTimer
from PyQt6.QtGui import QImage

log = logging.getLogger(__name__)

CAPTURE_TIMEOUT_S = 2.0
TOOL_PRECEDENCE = ("grim", "spectacle", "gnome-screenshot")


def pick_tool(which: Callable[[str], str | None] = shutil.which) -> str | None:
    """Returns the first installed capture tool in preference order."""
    return next((name for name in TOOL_PRECEDENCE if which(name)), None)


def output_command(output: str, path: str) -> list[str]:
    """Grabs one wl_output by name, so no crop is needed."""
    return ["grim", "-o", output, path]


def full_command(path: str) -> list[str]:
    """Grabs the whole virtual desktop; the caller crops each screen out of it."""
    return ["spectacle", "-b", "-n", "-f", "-o", path]


def whole_desktop_command(path: str) -> list[str]:
    """grim without -o captures every output into one image on wlroots."""
    return ["grim", path]


def gnome_command(path: str) -> list[str]:
    return ["gnome-screenshot", "-f", path]


def crop_rect_for_screen(geom: QRect, image_size: QSize) -> QRect:
    """Clips a screen rect to the image; an empty result means reject, never guess."""
    rect = geom.intersected(QRect(QPoint(0, 0), image_size))
    return QRect() if rect.isEmpty() else rect


def image_rect_for_screen(geometry: QRect, union: QRect, image_size: QSize) -> QRect:
    """Maps a logical screen rect into the device pixels of the whole-desktop image."""
    if union.width() <= 0 or union.height() <= 0:
        return QRect()
    scale_x = image_size.width() / union.width()
    scale_y = image_size.height() / union.height()
    rect = QRect(
        round((geometry.x() - union.x()) * scale_x),
        round((geometry.y() - union.y()) * scale_y),
        round(geometry.width() * scale_x),
        round(geometry.height() * scale_y),
    )
    return crop_rect_for_screen(rect, image_size)


def settle(delay_ms: int = 120):
    """Waits for the compositor to present the bare desktop, then drains paint events."""
    loop = QEventLoop()
    QTimer.singleShot(delay_ms, loop.quit)
    loop.exec()
    QCoreApplication.processEvents()


def _run_capture(build_command: Callable[[str], list[str]]) -> QImage:
    """Runs one tool into a private temp directory and returns the decoded image."""
    directory = tempfile.mkdtemp(prefix="ghalam_bg_")
    path = os.path.join(directory, "capture.png")
    command = build_command(path)
    try:
        subprocess.run(command, check=True, timeout=CAPTURE_TIMEOUT_S)
        image = QImage(path)
        if image.isNull():
            log.warning("Capture produced no image: %s", command)
        return image
    except (OSError, subprocess.SubprocessError) as exc:
        log.warning("Capture failed (%s): %s", command[0], exc)
        return QImage()
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def capture_output(output: str) -> QImage:
    """Grabs one output through grim; the caller falls back when this is null."""
    if not output or pick_tool() != "grim":
        return QImage()
    return _run_capture(lambda path: output_command(output, path))


def capture_desktop(screen_count: int) -> QImage:
    """Grabs the whole desktop once per capture pass, trying installed tools in order."""
    builders = []
    if shutil.which("spectacle"):
        builders.append(full_command)
    if shutil.which("grim"):
        builders.append(whole_desktop_command)
    if screen_count == 1 and shutil.which("gnome-screenshot"):
        builders.append(gnome_command)

    for build_command in builders:
        image = _run_capture(build_command)
        if not image.isNull():
            return image
    return QImage()
