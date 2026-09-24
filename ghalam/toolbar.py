"""
Glassmorphic floating toolbar for Screen Annotator with premium styling.
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QButtonGroup, 
    QFrame, QLabel, QToolTip, QGraphicsDropShadowEffect,
    QColorDialog
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import (
    QColor, QCursor, QFont, QPainter, QBrush, QPen, QLinearGradient, QGuiApplication
)
from .config import ToolType, PALETTE, DEFAULT_STROKE_WIDTH


class ColorButton(QPushButton):
    def __init__(self, color_info: dict, is_selected: bool = False, parent=None):
        super().__init__(parent)
        self.color_info = color_info
        self.color = color_info["color"]
        self.setFixedSize(22, 22)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip(f"{color_info['name']}")
        self.setCheckable(True)
        self.setChecked(is_selected)
        self.update_style()
        self.toggled.connect(lambda: self.update_style())

    def update_style(self):
        hex_code = self.color_info["hex"]
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {hex_code};
                    border: 2.5px solid #FFFFFF;
                    border-radius: 11px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {hex_code};
                    border: 1.5px solid rgba(255, 255, 255, 0.35);
                    border-radius: 11px;
                }}
                QPushButton:hover {{
                    border: 2px solid #FFFFFF;
                }}
            """)


class CustomColorButton(QPushButton):
    custom_color_changed = pyqtSignal(QColor)

    def __init__(self, initial_color: QColor = None, parent=None):
        super().__init__(parent)
        self.has_custom_color = initial_color is not None
        self.current_color = initial_color
        self.setFixedSize(22, 22)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setCheckable(True)
        self.update_tooltip()
        self.toggled.connect(lambda: self.update())

    def update_tooltip(self):
        if not self.has_custom_color:
            self.setToolTip("Pick Custom Color [8]\nClick to choose your own color")
        else:
            hex_code = self.current_color.name().upper()
            self.setToolTip(f"Custom Color ({hex_code}) [8]\nClick to select, click again or right-click to change")

    def set_color(self, color: QColor):
        if color.isValid():
            self.current_color = color
            self.has_custom_color = True
            self.update_tooltip()
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.pick_color()
            event.accept()
            return
        elif event.button() == Qt.MouseButton.LeftButton:
            if not self.has_custom_color or self.isChecked():
                # First time (no color picked yet) OR clicked while already selected
                self.pick_color()
                event.accept()
                return
        super().mousePressEvent(event)

    def pick_color(self):
        initial = self.current_color if self.has_custom_color else QColor("#FF2D55")
        dialog = QColorDialog(initial, self)
        dialog.setWindowTitle("Ghalam - Choose Color")
        dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
        dialog.setStyleSheet("""
            QColorDialog {
                background-color: #161A26;
                color: #FFFFFF;
            }
            QLabel {
                color: #CBD5E1;
                font-weight: 500;
            }
            QLineEdit {
                background-color: #0F121C;
                color: #FFFFFF;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 4px 8px;
            }
            QPushButton {
                background-color: #1E293B;
                color: #FFFFFF;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #334155;
                border: 1px solid #64748B;
            }
        """)
        if dialog.exec():
            chosen = dialog.selectedColor()
            if chosen.isValid():
                self.set_color(chosen)
                self.setChecked(True)
                self.custom_color_changed.emit(self.current_color)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect()
        w = rect.width()
        h = rect.height()
        circle_rect = QRectF(1.5, 1.5, w - 3, h - 3)

        if not self.has_custom_color:
            # Unset state: frosted glass outline with '+' icon
            bg_color = QColor(255, 255, 255, 26) if self.underMouse() else QColor(255, 255, 255, 12)
            painter.setBrush(QBrush(bg_color))
            border_color = QColor(255, 255, 255, 150) if self.underMouse() else QColor(255, 255, 255, 75)
            pen_style = Qt.PenStyle.SolidLine if self.underMouse() else Qt.PenStyle.DashLine
            painter.setPen(QPen(border_color, 1.4, pen_style))
            painter.drawEllipse(circle_rect)

            plus_color = QColor(255, 255, 255, 240) if self.underMouse() else QColor(255, 255, 255, 175)
            plus_pen = QPen(plus_color, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(plus_pen)
            cx, cy = w / 2.0, h / 2.0
            arm = 3.5
            painter.drawLine(QPointF(cx, cy - arm), QPointF(cx, cy + arm))
            painter.drawLine(QPointF(cx - arm, cy), QPointF(cx + arm, cy))
        else:
            # Set state: filled with custom color
            painter.setBrush(QBrush(self.current_color))

            if self.isChecked():
                painter.setPen(QPen(QColor(255, 255, 255), 2.5))
            elif self.underMouse():
                painter.setPen(QPen(QColor(255, 255, 255), 2.0))
            else:
                painter.setPen(QPen(QColor(255, 255, 255, 120), 1.5))

            painter.drawEllipse(circle_rect)

            # Contrast-aware '+' plus icon in center
            r, g, b = self.current_color.red(), self.current_color.green(), self.current_color.blue()
            luminance = 0.299 * r + 0.587 * g + 0.114 * b
            icon_color = QColor(0, 0, 0, 190) if luminance > 165 else QColor(255, 255, 255, 230)

            cx, cy = w / 2.0, h / 2.0
            arm = 3.5
            plus_pen = QPen(icon_color, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(plus_pen)
            painter.drawLine(QPointF(cx, cy - arm), QPointF(cx, cy + arm))
            painter.drawLine(QPointF(cx - arm, cy), QPointF(cx + arm, cy))

        painter.end()


class Toolbar(QWidget):
    tool_changed = pyqtSignal(ToolType)
    color_changed = pyqtSignal(QColor)
    stroke_changed = pyqtSignal(int)
    switch_monitor_requested = pyqtSignal()
    undo_requested = pyqtSignal()
    redo_requested = pyqtSignal()
    clear_requested = pyqtSignal()
    copy_requested = pyqtSignal()
    save_requested = pyqtSignal()
    exit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.drag_position = QPoint()
        self.current_stroke = DEFAULT_STROKE_WIDTH
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.init_ui()

    def init_ui(self):
        self.setObjectName("FloatingToolbar")
        self.setWindowFlags(Qt.WindowType.SubWindow)
        
        # Shadow effect for popping against any light or dark background
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(6)

        # Drag handle / Brand icon
        drag_handle = QLabel("✦")
        drag_handle.setObjectName("DragHandle")
        drag_handle.setToolTip("Drag toolbar anywhere")
        drag_handle.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        layout.addWidget(drag_handle)

        self.add_separator(layout)

        # Tool buttons group
        self.tool_group = QButtonGroup(self)
        self.tool_group.setExclusive(True)

        tools = [
            (ToolType.PEN, "✏️", "Pen (P)"),
            (ToolType.HIGHLIGHTER, "🖍️", "Highlighter (H)"),
            (ToolType.ARROW, "➔", "Arrow (A)"),
            (ToolType.RECTANGLE, "▢", "Rectangle (R)"),
            (ToolType.ELLIPSE, "○", "Circle (O)"),
            (ToolType.TEXT, "T", "Text (T)"),
            (ToolType.BADGE, "①", "Step Badge (N)"),
        ]

        for i, (tool_type, icon_str, tip) in enumerate(tools):
            btn = QPushButton(icon_str)
            btn.setCheckable(True)
            btn.setFixedSize(34, 34)
            btn.setToolTip(tip)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            if i == 0:
                btn.setChecked(True)
            self.tool_group.addButton(btn, tool_type.value)
            layout.addWidget(btn)

        self.tool_group.idClicked.connect(self._on_tool_clicked)

        self.add_separator(layout)

        # Color palette
        self.color_group = QButtonGroup(self)
        self.color_group.setExclusive(True)

        for i, color_data in enumerate(PALETTE):
            is_active = (i == 2)  # Default red/flame
            c_btn = ColorButton(color_data, is_selected=is_active)
            self.color_group.addButton(c_btn, i)
            layout.addWidget(c_btn)

        # 8th slot: Custom Color Picker button (unpicked by default)
        self.custom_color_btn = CustomColorButton(parent=self)
        self.color_group.addButton(self.custom_color_btn, len(PALETTE))
        layout.addWidget(self.custom_color_btn)
        self.custom_color_btn.custom_color_changed.connect(self.color_changed.emit)

        self.color_group.idClicked.connect(self._on_color_clicked)

        self.add_separator(layout)

        # Stroke width button (Latin digits only to prevent locale squishing)
        self.stroke_btn = QPushButton(f"{int(self.current_stroke)} px")
        self.stroke_btn.setObjectName("StrokeBtn")
        self.stroke_btn.setFixedSize(52, 34)
        self.stroke_btn.setToolTip("Stroke Size (or use Mouse Wheel)")
        self.stroke_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.stroke_btn.clicked.connect(self.cycle_stroke_width)
        layout.addWidget(self.stroke_btn)

        # Multi-monitor switch button (only if multiple screens connected)
        if len(QGuiApplication.screens()) > 1:
            self.monitor_btn = self.create_action_btn("🖥️", "Switch Monitor (M)", self.switch_monitor_requested.emit)
            layout.addWidget(self.monitor_btn)

        self.add_separator(layout)

        # Action buttons
        self.undo_btn = self.create_action_btn("↩", "Undo (Ctrl+Z)", self.undo_requested.emit)
        self.redo_btn = self.create_action_btn("↪", "Redo (Ctrl+Y)", self.redo_requested.emit)
        self.clear_btn = self.create_action_btn("🗑", "Clear All (C)", self.clear_requested.emit)
        self.copy_btn = self.create_action_btn("📋", "Copy Screen (Ctrl+C)", self.copy_requested.emit)
        self.save_btn = self.create_action_btn("💾", "Save to File (Ctrl+S)", self.save_requested.emit)
        
        self.close_btn = self.create_action_btn("✕", "Exit Annotator (Esc)", self.exit_requested.emit)
        self.close_btn.setObjectName("CloseBtn")

        layout.addWidget(self.undo_btn)
        layout.addWidget(self.redo_btn)
        layout.addWidget(self.clear_btn)
        layout.addWidget(self.copy_btn)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.close_btn)

        self.apply_theme()

    def add_separator(self, layout):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Plain)
        sep.setStyleSheet("background-color: rgba(255, 255, 255, 0.18); width: 1px; margin: 4px 4px;")
        layout.addWidget(sep)

    def create_action_btn(self, text, tooltip, callback):
        btn = QPushButton(text)
        btn.setFixedSize(34, 34)
        btn.setToolTip(tooltip)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.clicked.connect(callback)
        return btn

    def _on_tool_clicked(self, tool_id):
        for tool in ToolType:
            if tool.value == tool_id:
                self.tool_changed.emit(tool)
                break

    def _on_color_clicked(self, color_idx):
        if color_idx == len(PALETTE):
            if self.custom_color_btn.has_custom_color:
                self.color_changed.emit(self.custom_color_btn.current_color)
        elif 0 <= color_idx < len(PALETTE):
            self.color_changed.emit(PALETTE[color_idx]["color"])

    def select_tool(self, tool_type: ToolType):
        btn = self.tool_group.button(tool_type.value)
        if btn:
            btn.setChecked(True)
            self.tool_changed.emit(tool_type)

    def select_color_by_index(self, index: int):
        if index == len(PALETTE):
            if not self.custom_color_btn.has_custom_color:
                self.custom_color_btn.pick_color()
            else:
                self.custom_color_btn.setChecked(True)
                self.color_changed.emit(self.custom_color_btn.current_color)
        elif 0 <= index < len(PALETTE):
            btn = self.color_group.button(index)
            if btn:
                btn.setChecked(True)
                self.color_changed.emit(PALETTE[index]["color"])

    def set_stroke_width(self, width: int, emit_signal: bool = True):
        width = max(1, min(width, 40))
        if self.current_stroke == width:
            return
        self.current_stroke = width
        self.stroke_btn.setText(f"{int(self.current_stroke)} px")
        if emit_signal:
            self.stroke_changed.emit(self.current_stroke)

    def cycle_stroke_width(self):
        widths = [2, 4, 8, 14, 22]
        try:
            next_idx = (widths.index(self.current_stroke) + 1) % len(widths)
            new_width = widths[next_idx]
        except ValueError:
            new_width = 4
        self.set_stroke_width(new_width, emit_signal=True)

    def apply_theme(self):
        # Premium dark glass with solid contrast so it looks crisp on ANY background (white/dark)
        self.setStyleSheet("""
            QWidget#FloatingToolbar {
                background-color: rgba(15, 18, 28, 0.96);
                border: 1px solid rgba(255, 255, 255, 0.22);
                border-radius: 20px;
            }
            QLabel#DragHandle {
                color: #00E5FF;
                font-size: 17px;
                font-weight: bold;
                padding: 0 4px;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 9px;
                font-size: 14px;
                font-weight: bold;
                margin: 0px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.22);
                border: 1px solid rgba(255, 255, 255, 0.45);
            }
            QPushButton:checked {
                background-color: #00E5FF;
                color: #080C14;
                border: 1.5px solid #FFFFFF;
            }
            QPushButton#StrokeBtn {
                font-family: 'DejaVu Sans', 'Liberation Sans', sans-serif;
                font-size: 11px;
                font-weight: bold;
                color: #CBD5E1;
                background-color: rgba(255, 255, 255, 0.06);
            }
            QPushButton#StrokeBtn:hover {
                color: #FFFFFF;
                background-color: rgba(255, 255, 255, 0.18);
            }
            QPushButton#CloseBtn {
                background-color: rgba(255, 59, 48, 0.25);
                color: #FF5247;
                border: 1px solid rgba(255, 59, 48, 0.55);
            }
            QPushButton#CloseBtn:hover {
                background-color: #FF3B30;
                color: #FFFFFF;
                border: 1px solid #FF3B30;
            }
            QToolTip {
                background-color: #0B0E17;
                color: #FFFFFF;
                border: 1px solid #00E5FF;
                border-radius: 5px;
                padding: 5px 9px;
                font-size: 12px;
            }
        """)

    def paintEvent(self, event):
        # Custom painting ensures 100% solid, crisp glassmorphic card on any Qt platform / Wayland
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)

        # Solid dark obsidian gradient with 97% opacity
        grad = QLinearGradient(0, 0, 0, rect.height())
        grad.setColorAt(0.0, QColor(22, 26, 38, 248))
        grad.setColorAt(1.0, QColor(14, 17, 26, 250))
        painter.setBrush(QBrush(grad))

        # Distinct high-contrast border
        border_pen = QPen(QColor(255, 255, 255, 55), 1.2)
        painter.setPen(border_pen)
        painter.drawRoundedRect(rect, 19.0, 19.0)

        # Subtle top inner highlight
        inner_rect = rect.adjusted(1.0, 1.0, -1.0, -1.0)
        highlight_pen = QPen(QColor(255, 255, 255, 30), 1.0)
        painter.setPen(highlight_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(inner_rect, 18.0, 18.0)

        painter.end()

    # Dragging support
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            self.move(new_pos)
            event.accept()
