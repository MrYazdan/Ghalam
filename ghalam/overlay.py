"""
Fullscreen transparent overlay window hosting the canvas and floating toolbar.
"""
import os
from datetime import datetime

from PyQt6.QtCore import QEvent, QRect, Qt, QTimer, pyqtSignal
from PyQt6.QtDBus import QDBusConnection, QDBusInterface
from PyQt6.QtGui import QCursor, QGuiApplication, QImage, QKeyEvent, QPainter
from PyQt6.QtWidgets import QApplication, QFileDialog, QWidget

from .canvas import AnnotationCanvas
from .capture import capture_output, image_rect_for_screen, pick_tool, settle
from .config import ToolType
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
        self.capture_host = None
        self.init_window()
        self.init_ui()

    def init_window(self):
        # Window attributes for transparent top-level overlay on Wayland/X11
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setStyleSheet("background: transparent;")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        if QApplication.instance():
            QApplication.instance().installEventFilter(self)

    def focusNextPrevChild(self, next: bool) -> bool:
        return False

    def _owns_key_target(self, obj) -> bool:
        """True when the key target belongs to this overlay's widget tree."""
        return obj is self or (isinstance(obj, QWidget) and self.isAncestorOf(obj))

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress:
            # When typing in the inline text editor, do NOT intercept Tab or any key
            if hasattr(self, "canvas") and self.canvas.text_editor.isVisible():
                if event.key() == Qt.Key.Key_Escape:
                    self.canvas._commit_text()
                    return True
                return super().event(event)

            if QApplication.activeModalWidget() is not None:
                return super().event(event)

            if event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
                self.toggle_toolbar()
                return True
        return super().event(event)

    def eventFilter(self, obj, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress:
            # Do not intercept any shortcuts if user is typing in the inline text editor
            if hasattr(self, "canvas") and self.canvas.text_editor.isVisible():
                if event.key() == Qt.Key.Key_Escape:
                    self.canvas._commit_text()
                    return True
                return False

            # Keys aimed at another overlay, or at a modal dialog, are not ours.
            if not self._owns_key_target(obj) or QApplication.activeModalWidget() is not None:
                return False

            key = event.key()
            # Tab to toggle floating toolbar (Space and V removed)
            if key in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
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

        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        is_gnome = "gnome" in desktop or "ubuntu" in desktop

        if is_gnome:
            # On GNOME Wayland (Mutter), xdg_toplevel.set_fullscreen disables compositor alpha blending,
            # causing the background to render pitch black. Using show() with exact screen geometry
            # keeps the window frameless, on top, and fully transparent without Mutter unredirection.
            self.show()
            self.setGeometry(geom)
        else:
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
        """Reports the dismissal and closes; the owner decides whether to exit."""
        self.canvas.clear_all()
        self.dismiss_requested.emit()
        self.close()

    def closeEvent(self, event):
        """Leaf close: clears the canvas and never decides the process fate."""
        self.canvas.clear_all()
        event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()

        # If user is typing in inline text editor, do NOT trigger any shortcuts!
        if hasattr(self, "canvas") and self.canvas.text_editor.isVisible():
            if key == Qt.Key.Key_Escape:
                self.canvas._commit_text()
                event.accept()
                return
            super().keyPressEvent(event)
            return

        # A modal dialog owns every key while it is up.
        if QApplication.activeModalWidget() is not None:
            super().keyPressEvent(event)
            return

        # ESC: Instantly dismiss and clear everything
        if key == Qt.Key.Key_Escape:
            self.dismiss()
            event.accept()
            return

        # Tab: Toggle Toolbar visibility
        if key in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
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
        Captures this screen's desktop and composites the annotations on top.

        The host owns one hidden pass for every overlay; a standalone overlay hides
        only itself. Both paths restore the UI even when every capture tool fails.
        """
        if self.capture_host is not None:
            with self.capture_host.hidden_capture():
                return self._composite_image()

        self.hide()
        settle()
        try:
            return self._composite_image()
        finally:
            self.show_on_screen(self.target_screen)

    def _composite_image(self) -> QImage:
        width = self.canvas.width()
        height = self.canvas.height()
        result = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        result.fill(Qt.GlobalColor.transparent)

        background = self._grab_screen()
        if not background.isNull():
            painter = QPainter(result)
            painter.drawImage(QRect(0, 0, width, height), background)
            painter.end()

        painter = QPainter(result)
        self.canvas.render(painter)
        painter.end()
        return result

    def _grab_screen(self) -> QImage:
        screen = self.target_screen
        if screen is None and self.windowHandle() is not None:
            screen = self.windowHandle().screen()
        if screen is None:
            screen = self.screen()
        if screen is None:
            return QImage()

        if pick_tool() == "grim":
            image = capture_output(screen.name())
            if not image.isNull():
                return image

        if self.capture_host is not None:
            desktop = self.capture_host.desktop_screenshot()
            if not desktop.isNull():
                union = QRect()
                for other in QGuiApplication.screens():
                    union = union.united(other.geometry())
                rect = image_rect_for_screen(screen.geometry(), union, desktop.size())
                if not rect.isEmpty():
                    return desktop.copy(rect)

        # X11 root-window fallback. Wayland has no equivalent, so the pass ends empty.
        if QGuiApplication.platformName() != "wayland":
            pixmap = screen.grabWindow(0)
            if not pixmap.isNull():
                return pixmap.toImage()
        return QImage()

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
            self,
            "Save Annotation",
            default_file,
            "PNG Images (*.png);;All Files (*)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if self.toolbar_visible:
            self.toolbar.show()

        if file_path:
            img.save(file_path, "PNG")
            self.show_notification(f"✓ Saved to {os.path.basename(file_path)}")

    def show_notification(self, message: str):
        """Displays temporary notification message on toolbar."""
        original_text = self.toolbar.stroke_btn.text()
        self.toolbar.stroke_btn.setText(message[:14])
        QTimer.singleShot(1800, lambda: self.toolbar.stroke_btn.setText(original_text))
