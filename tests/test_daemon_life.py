"""
Daemon lifecycle: only AnnotatorApp decides when the process exits.

``QApplication.quit`` is replaced per test, so the assertion is the invariant itself
rather than a timing-dependent event loop race.
"""
import pytest
from PyQt6.QtGui import QColor

from ghalam.app import AnnotatorApp
from ghalam.config import ToolType

pytestmark = pytest.mark.gui


@pytest.fixture
def daemon(qapp, monkeypatch):
    app = AnnotatorApp(is_daemon=True)
    app.quit_calls = []
    monkeypatch.setattr(app.app, "quit", lambda: app.quit_calls.append(True))
    yield app
    app.hide_overlays()


def test_daemon_survives_dismiss(daemon):
    daemon.show_overlays()
    daemon.dismiss_all()
    assert daemon.quit_calls == []
    assert not daemon.is_any_overlay_visible()


def test_non_daemon_exits_on_dismiss(qapp, monkeypatch):
    app = AnnotatorApp(is_daemon=False)
    quit_calls = []
    monkeypatch.setattr(app.app, "quit", lambda: quit_calls.append(True))

    app.show_overlays()
    app.dismiss_all()

    assert quit_calls == [True]


def test_close_event_does_not_quit(daemon):
    daemon.show_overlays()
    daemon.overlays[0].close()
    assert daemon.quit_calls == []
    assert not daemon.is_any_overlay_visible()


def test_double_dismiss_is_idempotent(daemon):
    daemon.show_overlays()
    daemon.dismiss_all()
    daemon.dismiss_all()
    assert daemon.quit_calls == []
    assert not daemon.is_any_overlay_visible()


def test_pen_state_survives_cycle(daemon):
    daemon.show_overlays()
    toolbar = daemon.overlays[0].toolbar
    toolbar.select_tool(ToolType.ARROW)
    toolbar.select_color_by_index(1)
    toolbar.set_stroke_width(9)

    daemon.dismiss_all()
    daemon.show_overlays()

    restored = daemon.overlays[0]
    assert restored.toolbar.current_tool is ToolType.ARROW
    assert restored.toolbar.current_color == QColor("#00E5FF")
    assert restored.toolbar.current_stroke == 9
    assert restored.canvas.current_tool is ToolType.ARROW
    assert restored.canvas.current_color == QColor("#00E5FF")
    assert restored.canvas.stroke_width == 9
