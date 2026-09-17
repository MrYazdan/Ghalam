"""
Drawing canvas widget for rendering and capturing annotation strokes.
"""
from PyQt6.QtWidgets import QWidget, QLineEdit
from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QColor, QFont, QKeyEvent, QWheelEvent
from .config import ToolType, DEFAULT_TOOL, PALETTE, DEFAULT_COLOR_INDEX, DEFAULT_STROKE_WIDTH
from .models import DrawItem, StrokeItem, ArrowItem, RectItem, EllipseItem, BadgeItem, TextItem


class AnnotationCanvas(QWidget):
    stroke_width_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.current_tool = DEFAULT_TOOL
        self.current_color = PALETTE[DEFAULT_COLOR_INDEX]["color"]
        self.stroke_width = DEFAULT_STROKE_WIDTH

        self.items: list[DrawItem] = []
        self.redo_stack: list[DrawItem] = []
        self.current_item: DrawItem | None = None
        self.badge_counter = 1

        # Inline text editor for Text tool
        self.text_editor = QLineEdit(self)
        self.text_editor.hide()
        self.text_editor.returnPressed.connect(self._commit_text)
        self.text_editor_pos: QPointF | None = None

    def set_tool(self, tool: ToolType):
        self._commit_text()
        self.current_tool = tool
        self.update()

    def set_color(self, color: QColor):
        self.current_color = color
        self.update()

    def set_stroke_width(self, width: int, emit_signal: bool = True):
        width = max(1, min(width, 40))
        if self.stroke_width == width:
            return
        self.stroke_width = width
        if emit_signal:
            self.stroke_width_changed.emit(self.stroke_width)
        self.update()

    def undo(self):
        self._commit_text()
        if self.items:
            popped = self.items.pop()
            if isinstance(popped, BadgeItem) and self.badge_counter > 1:
                self.badge_counter -= 1
            self.redo_stack.append(popped)
            self.update()

    def redo(self):
        self._commit_text()
        if self.redo_stack:
            item = self.redo_stack.pop()
            if isinstance(item, BadgeItem):
                self.badge_counter += 1
            self.items.append(item)
            self.update()

    def clear_all(self):
        self._commit_text()
        self.items.clear()
        self.redo_stack.clear()
        self.badge_counter = 1
        self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        pos = event.position()
        self._commit_text()

        if self.current_tool == ToolType.PEN:
            self.current_item = StrokeItem([pos], self.current_color, self.stroke_width, is_highlighter=False)
        elif self.current_tool == ToolType.HIGHLIGHTER:
            self.current_item = StrokeItem([pos], self.current_color, self.stroke_width, is_highlighter=True)
        elif self.current_tool == ToolType.ARROW:
            self.current_item = ArrowItem(pos, pos, self.current_color, self.stroke_width)
        elif self.current_tool == ToolType.RECTANGLE:
            self.current_item = RectItem(pos, pos, self.current_color, self.stroke_width)
        elif self.current_tool == ToolType.ELLIPSE:
            self.current_item = EllipseItem(pos, pos, self.current_color, self.stroke_width)
        elif self.current_tool == ToolType.BADGE:
            badge = BadgeItem(pos, self.badge_counter, self.current_color)
            self.items.append(badge)
            self.redo_stack.clear()
            self.badge_counter += 1
            self.update()
            return
        elif self.current_tool == ToolType.TEXT:
            self._start_text_editor(pos)
            return

        self.update()

    def mouseMoveEvent(self, event):
        if not self.current_item or not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        pos = event.position()
        if isinstance(self.current_item, StrokeItem):
            self.current_item.add_point(pos)
        elif isinstance(self.current_item, (ArrowItem, RectItem, EllipseItem)):
            self.current_item.update_end(pos)

        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.current_item:
            self.items.append(self.current_item)
            self.redo_stack.clear()
            self.current_item = None
            self.update()

    def wheelEvent(self, event: QWheelEvent):
        # Adjust stroke width with mouse scroll wheel
        delta = event.angleDelta().y()
        if delta > 0:
            self.set_stroke_width(self.stroke_width + 1)
        elif delta < 0:
            self.set_stroke_width(self.stroke_width - 1)
        event.accept()

    def _start_text_editor(self, pos: QPointF):
        self.text_editor_pos = pos
        self.text_editor.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(15, 18, 26, 0.95);
                color: {self.current_color.name()};
                border: 2px solid {self.current_color.name()};
                border-radius: 6px;
                padding: 4px 8px;
                font-family: Sans Serif;
                font-size: 18px;
                font-weight: bold;
            }}
        """)
        self.text_editor.setFont(QFont("Sans Serif", 18, QFont.Weight.Bold))
        self.text_editor.setGeometry(int(pos.x()), int(pos.y()), 260, 36)
        self.text_editor.clear()
        self.text_editor.show()
        self.text_editor.setFocus()

    def _commit_text(self):
        if self.text_editor.isVisible():
            txt = self.text_editor.text().strip()
            if txt and self.text_editor_pos:
                item = TextItem(self.text_editor_pos, txt, self.current_color)
                self.items.append(item)
                self.redo_stack.clear()
            self.text_editor.clear()
            self.text_editor.hide()
            self.text_editor_pos = None
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        for item in self.items:
            item.draw(painter)
        if self.current_item:
            self.current_item.draw(painter)
