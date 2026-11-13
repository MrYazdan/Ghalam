"""Status toast: the full message is shown and disappears on its own."""
import pytest

from ghalam.overlay import OverlayWindow

pytestmark = pytest.mark.gui


@pytest.fixture
def overlay(qapp):
    window = OverlayWindow()
    window.resize(800, 600)
    window.show()
    yield window
    window.close()


def test_notification_shows_the_full_message(overlay):
    overlay.show_notification("Copied to clipboard!")

    assert overlay.toast.isVisible()
    assert overlay.toast_text.text() == "Copied to clipboard!"
    assert overlay.toast.width() >= overlay.toast_text.sizeHint().width()


def test_notification_hides_after_the_timeout(overlay, qtbot):
    overlay.show_notification("Saved")
    overlay.toast_timer.start(10)

    qtbot.waitUntil(lambda: not overlay.toast.isVisible(), timeout=1000)
