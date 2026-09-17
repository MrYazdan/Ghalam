"""
Configuration and constants for Screen Annotator.
"""
from enum import Enum, auto
from PyQt6.QtGui import QColor

class ToolType(Enum):
    PEN = auto()
    HIGHLIGHTER = auto()
    ARROW = auto()
    RECTANGLE = auto()
    ELLIPSE = auto()
    TEXT = auto()
    BADGE = auto()

# Premium curated modern color palette
PALETTE = [
    {"name": "Neon Green", "color": QColor("#00FF66"), "hex": "#00FF66"},
    {"name": "Cyber Cyan", "color": QColor("#00E5FF"), "hex": "#00E5FF"},
    {"name": "Flame Red", "color": QColor("#FF3B30"), "hex": "#FF3B30"},
    {"name": "Vibrant Yellow", "color": QColor("#FFD60A"), "hex": "#FFD60A"},
    {"name": "Sunset Orange", "color": QColor("#FF9500"), "hex": "#FF9500"},
    {"name": "Electric Purple", "color": QColor("#BF5AF2"), "hex": "#BF5AF2"},
    {"name": "Pure White", "color": QColor("#FFFFFF"), "hex": "#FFFFFF"},
]

DEFAULT_TOOL = ToolType.PEN
DEFAULT_COLOR_INDEX = 2  # Flame Red
DEFAULT_STROKE_WIDTH = 4
MIN_STROKE_WIDTH = 1
MAX_STROKE_WIDTH = 40
HIGHLIGHTER_ALPHA = 90

SOCKET_NAME = "ghalam_ipc_socket"
