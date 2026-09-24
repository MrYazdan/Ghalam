"""
Fullscreen transparent overlay window hosting the canvas and floating toolbar.
"""
import os
import subprocess
import tempfile
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QFileDialog, QApplication
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer, pyqtSignal, QEvent
from PyQt6.QtGui import (
    QGuiApplication, QCursor, QKeyEvent, QPainter, QImage, QPixmap
)
from PyQt6.QtDBus import QDBusInterface, QDBusConnection
from .config import ToolType
from .canvas import AnnotationCanvas
from .toolbar import Toolbar


def get_active_screen():
    """
    Accurately detects active monitor on KDE Plasma Wayland via KWin DBus.
    Falls back to cursor position or primary screen.
    """
    try:
        kwin = QDBusInterface("org.kde.KWin", "/KWin", "org.kde.KWin", QDBusConnection.sessionBus())
        if kwin.isValid():
            reply = kwin.call("activeOutputName")
            if reply.arguments():
                active_name = str(reply.arguments()[0]).strip()
                for s in QGuiApplication.screens():
                    if s.name() == active_name:
                        return s
    except Exception:
        pass

    cursor_pos = QCursor.pos()
    if cursor_pos.x() != 0 or cursor_pos.y() != 0:
        s = QGuiApplication.screenAt(cursor_pos)
        if s:
            return s

    screens = QGuiApplication.screens()
    return screens[0] if screens else QGuiApplication.primaryScreen()


class OverlayWindow(QWidget):
    dismiss_requested = pyqtSignal()

    def __init__(self, target_screen=None, parent=None):
        super().__init__(parent)
        self.target_screen = target_screen
        self.toolbar_visible = True
        self.init_window()
        self.init_ui()

    def init_window(self):
        # Window attributes for transparent top-level overlay on Wayland/X11
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        if QApplication.instance():
            QApplication.instance().installEventFilter(self)

    def focusNextPrevChild(self, next: bool) -> bool:
        return False

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
                self.toggle_toolbar()
                return True
        return super().event(event)

    def eventFilter(self, obj, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress:
            # Do not intercept if user is typing in the inline text editor
            if hasattr(self, "canvas") and self.canvas.text_editor.isVisible() and obj == self.canvas.text_editor:
                return super().eventFilter(obj, event)

            key = event.key()
            # Tab, Space, or V to toggle floating toolbar
            if key in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab, Qt.Key.Key_Space, Qt.Key.Key_V):
                self.toggle_toolbar()
                return True
            # ESC: Dismiss immediately from anywhere
            elif key == Qt.Key.Key_Escape:
                self.dismiss()
                return True

        return super().eventFilter(obj, event)

    def init_ui(self):
        # Canvas covering the entire overlay
        self.canvas = AnnotationCanvas(self)

        # Floating glassmorphic toolbar
        self.toolbar = Toolbar(self)

        # Wire signals between toolbar and canvas
        self.toolbar.tool_changed.connect(self.canvas.set_tool)
        self.toolbar.color_changed.connect(self.canvas.set_color)
        self.toolbar.stroke_changed.connect(lambda w: self.canvas.set_stroke_width(w, emit_signal=False))
        self.toolbar.switch_monitor_requested.connect(self.switch_screen)
        self.canvas.stroke_width_changed.connect(lambda w: self.toolbar.set_stroke_width(w, emit_signal=False))

        self.toolbar.undo_requested.connect(self.canvas.undo)
        self.toolbar.redo_requested.connect(self.canvas.redo)
        self.toolbar.clear_requested.connect(self.canvas.clear_all)
        self.toolbar.copy_requested.connect(self.copy_to_clipboard)
        self.toolbar.save_requested.connect(self.save_to_file)
        self.toolbar.exit_requested.connect(self.dismiss)

    def show_on_screen(self, target_screen):
        """Displays overlay specifically on target_screen with proper Wayland output mapping."""
        self.target_screen = target_screen
        self.hide()
        self.winId()  # Forces native QWindow creation
        wh = self.windowHandle()
        if wh:
            wh.setScreen(target_screen)

        geom = target_screen.geometry()
        self.setGeometry(geom)
        self.canvas.setGeometry(0, 0, geom.width(), geom.height())

        # Reposition and display toolbar by default
        self.reposition_toolbar()
        if self.toolbar_visible:
            self.toolbar.show()
            self.toolbar.raise_()
        else:
            self.toolbar.hide()

        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def reposition_toolbar(self):
        """Calculates natural size and centers toolbar at the bottom."""
        self.toolbar.adjustSize()
        hint = self.toolbar.sizeHint()
        geom = self.geometry()
        tb_width = min(hint.width() + 16, geom.width() - 40)
        tb_height = hint.height() + 8
        tb_x = (geom.width() - tb_width) // 2
        tb_y = geom.height() - tb_height - 35
        self.toolbar.setGeometry(tb_x, tb_y, tb_width, tb_height)

    def toggle_toolbar(self):
        """Toggles floating toolbar visibility on/off (Tab key)."""
        if self.toolbar.isVisible():
            self.toolbar.hide()
            self.toolbar_visible = False
        else:
            self.reposition_toolbar()
            self.toolbar.show()
            self.toolbar.raise_()
            self.toolbar_visible = True

    def show_on_active_screen(self):
        """Displays overlay on currently active monitor."""
        target = self.target_screen or get_active_screen()
        self.show_on_screen(target)

    def switch_screen(self):
        """Switches overlay between connected monitors on Wayland."""
        screens = QGuiApplication.screens()
        if len(screens) <= 1:
            return

        current_screen = None
        if self.windowHandle():
            current_screen = self.windowHandle().screen()
        if not current_screen:
            current_screen = self.target_screen or self.screen()

        try:
            current_idx = screens.index(current_screen)
        except ValueError:
            current_idx = 0

        next_idx = (current_idx + 1) % len(screens)
        next_screen = screens[next_idx]
        self.show_on_screen(next_screen)
        self.show_notification(f"Monitor {next_idx + 1}: {next_screen.name()}")

    def dismiss(self):
        """Immediately clear everything and exit completely."""
        self.canvas.clear_all()
        self.dismiss_requested.emit()
        self.close()
        QApplication.quit()

    def closeEvent(self, event):
        """Ensure full application termination on window close."""
        self.canvas.clear_all()
        QApplication.quit()
        event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()

        # ESC: Instantly dismiss and clear everything
        if key == Qt.Key.Key_Escape:
            self.dismiss()
            event.accept()
            return

        # Tab: Toggle Toolbar visibility
        if key == Qt.Key.Key_Tab:
            self.toggle_toolbar()
            event.accept()
            return

        # M: Switch monitor
        if key == Qt.Key.Key_M:
            self.switch_screen()
            event.accept()
            return

        # Undo: Ctrl+Z
        if modifiers & Qt.KeyboardModifier.ControlModifier and not (modifiers & Qt.KeyboardModifier.ShiftModifier):
            if key == Qt.Key.Key_Z:
                self.canvas.undo()
                event.accept()
                return
            elif key == Qt.Key.Key_C:
                self.copy_to_clipboard()
                event.accept()
                return
            elif key == Qt.Key.Key_S:
                self.save_to_file()
                event.accept()
                return

        # Redo: Ctrl+Shift+Z or Ctrl+Y
        if (modifiers & Qt.KeyboardModifier.ControlModifier and modifiers & Qt.KeyboardModifier.ShiftModifier and key == Qt.Key.Key_Z) or \
           (modifiers & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_Y):
            self.canvas.redo()
            event.accept()
            return

        # Tool shortcuts
        if key == Qt.Key.Key_P:
            self.toolbar.select_tool(ToolType.PEN)
        elif key == Qt.Key.Key_H:
            self.toolbar.select_tool(ToolType.HIGHLIGHTER)
        elif key == Qt.Key.Key_A:
            self.toolbar.select_tool(ToolType.ARROW)
        elif key == Qt.Key.Key_R:
            self.toolbar.select_tool(ToolType.RECTANGLE)
        elif key == Qt.Key.Key_O:
            self.toolbar.select_tool(ToolType.ELLIPSE)
        elif key == Qt.Key.Key_T:
            self.toolbar.select_tool(ToolType.TEXT)
        elif key == Qt.Key.Key_N:
            self.toolbar.select_tool(ToolType.BADGE)
        elif key == Qt.Key.Key_C:
            self.canvas.clear_all()
        # Number keys 1-8 for color presets (8 is custom color)
        elif Qt.Key.Key_1 <= key <= Qt.Key.Key_8:
            color_index = key - Qt.Key.Key_1
            self.toolbar.select_color_by_index(color_index)
        else:
            super().keyPressEvent(event)

    def capture_composite_image(self) -> QImage:
        """
        Captures the underlying desktop background (via spectacle on KDE Wayland)
        and composites the drawn annotations on top.
        """
        w = self.canvas.width()
        h = self.canvas.height()
        result_img = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
        result_img.fill(Qt.GlobalColor.transparent)

        bg_captured = False
        temp_path = os.path.join(tempfile.gettempdir(), f"annotator_bg_{os.getpid()}.png")
        try:
            self.toolbar.hide()
            QGuiApplication.processEvents()

            subprocess.run([
                "spectacle", "-b", "-n", "-m", "-o", temp_path
            ], check=True, timeout=2.0)

            if os.path.exists(temp_path):
                bg_img = QImage(temp_path)
                painter = QPainter(result_img)
                painter.drawImage(0, 0, bg_img)
                painter.end()
                os.remove(temp_path)
                bg_captured = True
        except Exception:
            pass
        finally:
            if self.toolbar_visible:
                self.toolbar.show()

        # Universal fallback for Windows, macOS, and X11 where grabWindow(0) is natively supported
        if not bg_captured:
            try:
                screen = self.windowHandle().screen() if self.windowHandle() else self.screen()
                if screen:
                    pix = screen.grabWindow(0)
                    if not pix.isNull() and pix.width() > 0:
                        painter = QPainter(result_img)
                        painter.drawPixmap(0, 0, pix)
                        painter.end()
            except Exception:
                pass

        painter = QPainter(result_img)
        self.canvas.render(painter)
        painter.end()

        return result_img

    def copy_to_clipboard(self):
        """Copies composite image to system clipboard."""
        img = self.capture_composite_image()
        clipboard = QGuiApplication.clipboard()
        clipboard.setImage(img)
        self.show_notification("✓ Copied to clipboard!")

    def save_to_file(self):
        """Saves composite screenshot to Pictures directory or prompt."""
        img = self.capture_composite_image()
        pics_dir = os.path.expanduser("~/Pictures/Screenshots")
        os.makedirs(pics_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        default_file = os.path.join(pics_dir, f"annotation_{timestamp}.png")

        self.toolbar.hide()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Annotation", default_file, "PNG Images (*.png);;All Files (*)"
        )
        self.toolbar.show()

        if file_path:
            img.save(file_path, "PNG")
            self.show_notification(f"✓ Saved to {os.path.basename(file_path)}")

    def show_notification(self, message: str):
        """Displays temporary notification message on toolbar."""
        original_text = self.toolbar.stroke_btn.text()
        self.toolbar.stroke_btn.setText(message[:14])
        QTimer.singleShot(1800, lambda: self.toolbar.stroke_btn.setText(original_text))
