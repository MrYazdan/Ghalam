"""Annotation text: one point size for the inline editor and the committed item."""
import pytest
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor, QFont, QFontMetrics

from ghalam.canvas import AnnotationCanvas
from ghalam.config import FONT_FAMILY, TEXT_FONT_SIZE_PT
from ghalam.models import TextItem

pytestmark = pytest.mark.gui


def test_editor_uses_points_not_pixels(qapp):
    canvas = AnnotationCanvas()
    canvas._start_text_editor(QPointF(10, 10))

    assert canvas.text_editor.font().pointSizeF() == TEXT_FONT_SIZE_PT
    assert f"font-size: {TEXT_FONT_SIZE_PT}pt;" in canvas.text_editor.styleSheet()
    assert f"font-size: {TEXT_FONT_SIZE_PT}px" not in canvas.text_editor.styleSheet()


def test_text_item_defaults_to_the_same_size():
    assert TextItem(QPointF(0, 0), "x", QColor("#FFFFFF")).font_size == TEXT_FONT_SIZE_PT


def test_metrics_agree_within_one_pixel(qapp):
    canvas = AnnotationCanvas()
    canvas._start_text_editor(QPointF(10, 10))
    committed = QFont(FONT_FAMILY, TEXT_FONT_SIZE_PT, QFont.Weight.Bold)

    editor_height = QFontMetrics(canvas.text_editor.font()).height()
    committed_height = QFontMetrics(committed).height()
    assert abs(editor_height - committed_height) <= 1
