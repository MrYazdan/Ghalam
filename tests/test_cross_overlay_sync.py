"""Cross-overlay sync: a wheel notch on one screen reaches every toolbar."""
import pytest
from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QGuiApplication, QWheelEvent
from PyQt6.QtWidgets import QApplication

from ghalam.app import AnnotatorApp

pytestmark = pytest.mark.gui


def _wheel(canvas):
    event = QWheelEvent(
        QPointF(10, 10),
        QPointF(10, 10),
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    QApplication.sendEvent(canvas, event)


@pytest.fixture
def two_overlays(qapp, monkeypatch):
    app = AnnotatorApp(is_daemon=True)
    screen = QGuiApplication.primaryScreen()
    monkeypatch.setattr(app, "resolve_target_screens", lambda: [screen, screen])
    app.show_overlays()
    yield app
    app.hide_overlays()


def test_wheel_on_one_overlay_reaches_the_other_toolbar(two_overlays):
    first, second = two_overlays.overlays
    start = first.canvas.stroke_width

    for _ in range(3):
        _wheel(first.canvas)

    assert first.canvas.stroke_width == start + 3
    assert second.toolbar.current_stroke == start + 3
    assert second.toolbar.stroke_btn.text() == f"{start + 3} px"


def test_wheel_does_not_echo_back(two_overlays):
    first, second = two_overlays.overlays
    start = second.canvas.stroke_width
    emitted = []
    second.canvas.stroke_width_changed.connect(emitted.append)

    _wheel(first.canvas)

    assert emitted == []
    assert second.canvas.stroke_width == start
