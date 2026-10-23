"""
Bundled offline font loading (Vazirmatn - open-source Persian typeface).

The TTF faces live in ``assets/fonts/`` and are registered with Qt at runtime, so
no system-wide installation is required and the app works fully offline / frozen.
"""
import logging
import os

from PyQt6.QtGui import QFontDatabase, QGuiApplication

from .config import FONT_FAMILY, FONT_WEIGHTS, get_asset_path

log = logging.getLogger(__name__)

_loaded = False


def load_fonts() -> str:
    """
    Registers the bundled Vazirmatn faces with the Qt font database.

    Must be called *after* a QApplication/QGuiApplication instance exists, because
    QFontDatabase needs a live application (calling it earlier crashes the process).
    Safe to call multiple times: registration only happens on the first successful
    call. If no bundled face could be registered the system font is used instead and
    a warning is logged, so the next call retries. Returns the family name to use.
    """
    global _loaded
    if _loaded:
        return FONT_FAMILY
    if QGuiApplication.instance() is None:
        raise RuntimeError("load_fonts() must be called after a QGuiApplication instance exists")

    registered = 0
    for weight in FONT_WEIGHTS:
        path = get_asset_path(os.path.join("fonts", f"Vazirmatn-{weight}.ttf"))
        if not os.path.exists(path):
            log.warning("Bundled font missing: %s", path)
            continue
        if QFontDatabase.addApplicationFont(path) == -1:
            log.warning("Qt refused to register bundled font: %s", path)
            continue
        registered += 1

    if not registered:
        log.warning("No %s faces registered, falling back to the system font", FONT_FAMILY)
        return FONT_FAMILY

    _loaded = True
    return FONT_FAMILY
