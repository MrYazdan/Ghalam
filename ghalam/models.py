"""
Drawing models representing canvas annotation elements.
"""
import math
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
from .config import HIGHLIGHTER_ALPHA

class DrawItem:
    def draw(self, painter: QPainter):
        raise NotImplementedError


class StrokeItem(DrawItem):
    def __init__(self, points: list[QPointF], color: QColor, width: int, is_highlighter: bool = False):
        self.points = list(points)
        self.color = QColor(color)
        self.width = width
        self.is_highlighter = is_highlighter
        if self.is_highlighter:
            self.color.setAlpha(HIGHLIGHTER_ALPHA)
            self.width = max(width * 3, 16)

    def add_point(self, pt: QPointF):
        self.points.append(pt)

    def draw(self, painter: QPainter):
        if not self.points:
            return
        
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        pen = QPen(self.color, self.width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if len(self.points) == 1:
            painter.drawPoint(self.points[0])
        elif len(self.points) == 2:
            painter.drawLine(self.points[0], self.points[1])
        else:
            path = QPainterPath()
            path.moveTo(self.points[0])
            for i in range(1, len(self.points) - 1):
                p0 = self.points[i]
                p1 = self.points[i + 1]
                mid = QPointF((p0.x() + p1.x()) / 2.0, (p0.y() + p1.y()) / 2.0)
                path.quadTo(p0, mid)
            path.lineTo(self.points[-1])
            painter.drawPath(path)

        painter.restore()


class ArrowItem(DrawItem):
    def __init__(self, start: QPointF, end: QPointF, color: QColor, width: int):
        self.start = start
        self.end = end
        self.color = QColor(color)
        self.width = width

    def update_end(self, end: QPointF):
        self.end = end

    def draw(self, painter: QPainter):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        pen = QPen(self.color, self.width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        dx = self.end.x() - self.start.x()
        dy = self.end.y() - self.start.y()
        length = math.hypot(dx, dy)
        if length < 4:
            painter.drawLine(self.start, self.end)
            painter.restore()
            return

        angle = math.atan2(dy, dx)
        head_length = max(self.width * 3.5, 16.0)
        head_length = min(head_length, length * 0.45)
        head_angle = math.radians(28)

        # Draw main stem up to arrowhead base
        arrow_base_x = self.end.x() - head_length * math.cos(angle)
        arrow_base_y = self.end.y() - head_length * math.sin(angle)
        painter.drawLine(self.start, QPointF(arrow_base_x, arrow_base_y))

        # Draw filled triangle arrowhead
        left = QPointF(
            self.end.x() - head_length * math.cos(angle - head_angle),
            self.end.y() - head_length * math.sin(angle - head_angle)
        )
        right = QPointF(
            self.end.x() - head_length * math.cos(angle + head_angle),
            self.end.y() - head_length * math.sin(angle + head_angle)
        )

        path = QPainterPath()
        path.moveTo(self.end)
        path.lineTo(left)
        path.lineTo(right)
        path.closeSubpath()

        painter.setBrush(QBrush(self.color))
        painter.drawPath(path)
        painter.restore()


class RectItem(DrawItem):
    def __init__(self, start: QPointF, end: QPointF, color: QColor, width: int):
        self.start = start
        self.end = end
        self.color = QColor(color)
        self.width = width

    def update_end(self, end: QPointF):
        self.end = end

    def draw(self, painter: QPainter):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        pen = QPen(self.color, self.width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        rect = QRectF(self.start, self.end).normalized()
        painter.drawRoundedRect(rect, 8.0, 8.0)
        painter.restore()


class EllipseItem(DrawItem):
    def __init__(self, start: QPointF, end: QPointF, color: QColor, width: int):
        self.start = start
        self.end = end
        self.color = QColor(color)
        self.width = width

    def update_end(self, end: QPointF):
        self.end = end

    def draw(self, painter: QPainter):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        pen = QPen(self.color, self.width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        rect = QRectF(self.start, self.end).normalized()
        painter.drawEllipse(rect)
        painter.restore()


class BadgeItem(DrawItem):
    def __init__(self, center: QPointF, number: int, color: QColor, radius: float = 16.0):
        self.center = center
        self.number = number
        self.color = QColor(color)
        self.radius = radius

    def draw(self, painter: QPainter):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Shadow
        shadow_rect = QRectF(
            self.center.x() - self.radius + 1.5,
            self.center.y() - self.radius + 2.0,
            self.radius * 2,
            self.radius * 2
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 90)))
        painter.drawEllipse(shadow_rect)

        # Main filled circle
        circle_rect = QRectF(
            self.center.x() - self.radius,
            self.center.y() - self.radius,
            self.radius * 2,
            self.radius * 2
        )
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(QColor(255, 255, 255, 220), 2.0))
        painter.drawEllipse(circle_rect)

        # Number text in contrast color
        # Determine contrast color (black or white)
        luminance = (0.299 * self.color.red() + 0.587 * self.color.green() + 0.114 * self.color.blue()) / 255
        text_color = QColor(0, 0, 0) if luminance > 0.6 else QColor(255, 255, 255)

        painter.setPen(text_color)
        font = QFont("Sans Serif", int(self.radius * 0.9), QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(circle_rect, Qt.AlignmentFlag.AlignCenter, str(self.number))

        painter.restore()


class TextItem(DrawItem):
    def __init__(self, pos: QPointF, text: str, color: QColor, font_size: int = 18):
        self.pos = pos
        self.text = text
        self.color = QColor(color)
        self.font_size = font_size

    def draw(self, painter: QPainter):
        if not self.text.strip():
            return
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        font = QFont("Sans Serif", self.font_size, QFont.Weight.Bold)
        painter.setFont(font)

        metrics = painter.fontMetrics()
        lines = self.text.split("\n")
        line_height = metrics.lineSpacing()
        total_height = line_height * len(lines)
        max_width = max(metrics.horizontalAdvance(l) for l in lines) if lines else 0

        padding = 6
        bg_rect = QRectF(
            self.pos.x() - padding,
            self.pos.y() - padding,
            max_width + padding * 2,
            total_height + padding * 2
        )

        # Draw sleek dark pill background for readability
        painter.setPen(QPen(QColor(self.color.red(), self.color.green(), self.color.blue(), 100), 1.5))
        painter.setBrush(QBrush(QColor(15, 18, 26, 215)))
        painter.drawRoundedRect(bg_rect, 6.0, 6.0)

        # Draw text lines
        painter.setPen(self.color)
        y = self.pos.y() + metrics.ascent()
        for line in lines:
            painter.drawText(int(self.pos.x()), int(y), line)
            y += line_height

        painter.restore()
