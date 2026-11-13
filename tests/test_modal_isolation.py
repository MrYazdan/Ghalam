"""
Modal input isolation: Esc belongs to the dialog that is actually on top.

Every overlay installs an application-wide key filter, so these tests exercise the
real filter rather than calling the guard directly.
"""
import pytest
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QColorDialog, QFileDialog

from ghalam.models import StrokeItem
from ghalam.overlay import OverlayWindow

pytestmark = pytest.mark.gui


@pytest.fixture
def overlay(qapp):
    window = OverlayWindow()
    window.show()
    window.canvas.items.append(
        StrokeItem([QPointF(10, 10), QPointF(30, 30)], QColor("#FF3B30"), 4)
    )
    yield window
    window.close()


def _press_escape_in(dialog, qtbot):
    dialog.open()
    qtbot.waitUntil(dialog.isVisible, timeout=1000)
    QTest.keyClick(dialog, Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: not dialog.isVisible(), timeout=1000)


def test_escape_in_the_save_dialog_keeps_the_drawing(overlay, qtbot):
    dialog = QFileDialog(overlay)
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)

    _press_escape_in(dialog, qtbot)

    assert len(overlay.canvas.items) == 1
    assert overlay.isVisible()


def test_escape_in_the_colour_dialog_keeps_the_drawing(overlay, qtbot):
    dialog = QColorDialog(QColor("#00E5FF"), overlay)
    dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)

    _press_escape_in(dialog, qtbot)

    assert len(overlay.canvas.items) == 1
    assert overlay.isVisible()


def test_escape_without_a_dialog_still_dismisses(overlay, qtbot):
    dismissed = []
    overlay.dismiss_requested.connect(lambda: dismissed.append(True))
    overlay.activateWindow()
    overlay.setFocus()

    QTest.keyClick(overlay, Qt.Key.Key_Escape)

    assert dismissed == [True]
    assert not overlay.isVisible()
    assert overlay.canvas.items == []


def test_escape_commits_the_inline_text(overlay, qtbot):
    overlay.canvas._start_text_editor(QPointF(20, 20))
    overlay.canvas.text_editor.setText("hello")

    QTest.keyClick(overlay.canvas.text_editor, Qt.Key.Key_Escape)

    assert overlay.canvas.text_editor.isHidden()
    assert any(type(item).__name__ == "TextItem" for item in overlay.canvas.items)
