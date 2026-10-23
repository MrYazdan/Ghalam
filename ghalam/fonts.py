"""
Bundled offline font loading (Vazirmatn - open-source Persian typeface).

The TTF faces live in ``assets/fonts/`` and are registered with Qt at runtime, so
no system-wide installation is required and the app works fully offline / frozen.
"""
import os

from PyQt6.QtGui import QFont, QFontDatabase

from .config import FONT_FAMILY, FONT_WEIGHTS, get_asset_path

_loaded = False


def load_fonts() -> str:
    """
    Registers the bundled Vazirmatn faces with the Qt font database.

    Safe to call multiple times (idempotent). Must be called *after* a
    QApplication/QGuiApplication instance exists. Returns the family name to use.
    """
    global _loaded
    if _loaded:
        return FONT_FAMILY

    for weight in FONT_WEIGHTS:
        path = get_asset_path(os.path.join("fonts", f"Vazirmatn-{weight}.ttf"))
        if os.path.exists(path):
            QFontDatabase.addApplicationFont(path)

    _loaded = True
    return FONT_FAMILY


def make_font(point_size: int = -1, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """
    Returns a QFont using the bundled Vazirmatn family with sensible defaults.

    ``point_size`` of -1 keeps the application/system default size.
    """
    font = QFont(FONT_FAMILY)
    if point_size > 0:
        font.setPointSize(point_size)
    font.setWeight(weight)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    return font
