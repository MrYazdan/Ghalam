"""Bundled icons: files, tool table, renderer and the absence of glyph text."""
import ast
from pathlib import Path

import pytest

from ghalam import icons
from ghalam.toolbar import TOOL_BUTTONS

ROOT = Path(__file__).resolve().parents[1]


def test_every_icon_has_a_file():
    for name in icons.ICON_NAMES:
        assert Path(icons.icon_path(name)).is_file()


def test_tool_buttons_use_known_icons():
    assert len(TOOL_BUTTONS) == 7
    for _, icon_name, _ in TOOL_BUTTONS:
        assert icon_name in icons.ICON_NAMES


def test_every_svg_keeps_the_colour_token():
    for name in icons.ICON_NAMES:
        assert b"#FFFFFF" in Path(icons.icon_path(name)).read_bytes()


def test_render_pixmap_is_visible(qapp):
    image = icons.render_pixmap("pen", "#FFFFFF", 18).toImage()
    assert any(
        image.pixelColor(x, y).alpha() > 0
        for x in range(image.width())
        for y in range(image.height())
    )


def test_load_icon_has_normal_and_hidpi_sizes(qapp):
    icon = icons.load_icon("pen")
    assert {size.width() for size in icon.availableSizes()} == {18, 36}


def _widget_text_literals(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        if name in {"QPushButton", "QLabel"} and node.args:
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                yield arg.value
        elif name in {"setText", "drawText"}:
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    yield arg.value


@pytest.mark.parametrize("module", ["toolbar.py", "app.py", "overlay.py"])
def test_widget_text_is_ascii(module):
    literals = list(_widget_text_literals(ROOT / "ghalam" / module))
    non_ascii = [text for text in literals if not text.isascii()]
    assert non_ascii == []
