"""
Bundled SVG icon rendering for the toolbar, tray and toasts.

The assets are stroke-only and carry a literal ``#FFFFFF`` token, which is rewritten
in memory for the normal, checked and hover states. Rendering through QSvgRenderer
avoids QIcon(path), which would require Qt's qsvg image plugin inside a frozen bundle.
"""
import os
from functools import lru_cache

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

from .config import get_asset_path

ICON_NAMES = (
    "brand",
    "pen",
    "highlighter",
    "arrow",
    "rectangle",
    "ellipse",
    "text",
    "badge",
    "monitor",
    "undo",
    "redo",
    "clear",
    "copy",
    "save",
    "close",
    "check",
)

_COLOR_TOKEN = b"#FFFFFF"


def icon_path(name: str) -> str:
    """Returns the absolute path of a bundled icon, rejecting unknown names."""
    if name not in ICON_NAMES:
        raise ValueError(f"unknown icon: {name}")
    return get_asset_path(os.path.join("icons", f"{name}.svg"))


@lru_cache(maxsize=None)
def _renderer(name: str, color: str) -> QSvgRenderer:
    path = icon_path(name)
    with open(path, "rb") as handle:
        data = handle.read()
    if _COLOR_TOKEN not in data:
        raise ValueError(f"{path} is missing the {_COLOR_TOKEN.decode()} token")
    return QSvgRenderer(QByteArray(data.replace(_COLOR_TOKEN, color.encode("ascii"))))


def render_pixmap(name: str, color: str, size: int = 18) -> QPixmap:
    """Renders one icon at ``size`` device pixels in ``color``."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    _renderer(name, color).render(painter)
    painter.end()
    return pixmap


def load_icon(
    name: str,
    size: int = 18,
    off: str = "#FFFFFF",
    on: str = "#080C14",
    active: str | None = None,
) -> QIcon:
    """Builds a QIcon with normal, checked and optional hover pixmaps at 1x and 2x."""
    icon = QIcon()
    for scale in (1, 2):
        pixels = size * scale
        icon.addPixmap(render_pixmap(name, off, pixels), QIcon.Mode.Normal, QIcon.State.Off)
        icon.addPixmap(render_pixmap(name, on, pixels), QIcon.Mode.Normal, QIcon.State.On)
        if active is not None:
            icon.addPixmap(render_pixmap(name, active, pixels), QIcon.Mode.Active, QIcon.State.Off)
            icon.addPixmap(render_pixmap(name, active, pixels), QIcon.Mode.Active, QIcon.State.On)
    return icon
