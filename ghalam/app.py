"""
Application lifecycle, multi-monitor management, and single-instance IPC.
"""
import sys
import signal
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QGuiApplication
from PyQt6.QtCore import Qt, QTimer
from .config import SOCKET_NAME
from .overlay import OverlayWindow, get_active_screen


def create_tray_icon_pixmap() -> QPixmap:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setBrush(QColor("#00E5FF"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(4, 4, 24, 24)
    p.setPen(QColor("#0A0E1A"))
    p.setFont(p.font())
    p.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "✦")
    p.end()
    return pixmap


class AnnotatorApp:
    def __init__(self, is_daemon: bool = False, monitor_target: str = "active"):
        # Ensure Ctrl+C terminates Python instantly from terminal
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setApplicationName("Ghalam")
        self.is_daemon = is_daemon
        self.monitor_target = monitor_target

        if self.is_daemon:
            self.app.setQuitOnLastWindowClosed(False)
        else:
            self.app.setQuitOnLastWindowClosed(True)

        # Periodic timer allowing Python interpreter to process OS signals
        self.sig_timer = QTimer()
        self.sig_timer.start(200)
        self.sig_timer.timeout.connect(lambda: None)

        self.overlays: list[OverlayWindow] = []
        self.server = None
        self.tray = None

    @staticmethod
    def send_ipc_command(command: str = "SHOW") -> bool:
        """Sends command to existing instance if running. Returns True if connected."""
        socket = QLocalSocket()
        socket.connectToServer(SOCKET_NAME)
        if socket.waitForConnected(300):
            socket.write(command.encode("utf-8"))
            socket.waitForBytesWritten(300)
            socket.disconnectFromServer()
            return True
        return False

    def start_server(self):
        QLocalServer.removeServer(SOCKET_NAME)
        self.server = QLocalServer()
        self.server.listen(SOCKET_NAME)
        self.server.newConnection.connect(self._handle_client_connection)

    def _handle_client_connection(self):
        client = self.server.nextPendingConnection()
        if client:
            client.waitForReadyRead(200)
            cmd = bytes(client.readAll()).decode("utf-8").strip()
            client.disconnectFromServer()

            if cmd in ("SHOW", "TOGGLE"):
                if self.is_any_overlay_visible():
                    self.dismiss_all()
                else:
                    self.show_overlays()
            elif cmd == "QUIT":
                self.app.quit()

    def is_any_overlay_visible(self) -> bool:
        return any(ov.isVisible() for ov in self.overlays)

    def dismiss_all(self):
        for ov in self.overlays:
            ov.canvas.clear_all()
            ov.close()
        if not self.is_daemon:
            self.app.quit()

    def resolve_target_screens(self) -> list:
        screens = QGuiApplication.screens()
        if not screens:
            return []

        target = self.monitor_target.lower().strip()
        if target == "all":
            return list(screens)
        elif target == "hdmi":
            for s in screens:
                if "hdmi" in s.name().lower():
                    return [s]
        elif target == "dp":
            for s in screens:
                if "dp" in s.name().lower():
                    return [s]
        elif target.isdigit():
            idx = int(target)
            if 0 <= idx < len(screens):
                return [screens[idx]]

        # Default: active screen via KWin DBus
        active = get_active_screen()
        return [active]

    def show_overlays(self):
        self.dismiss_all()
        target_screens = self.resolve_target_screens()
        self.overlays = []

        for screen in target_screens:
            ov = OverlayWindow(target_screen=screen)
            ov.dismiss_requested.connect(self.dismiss_all)
            ov.toolbar.exit_requested.connect(self.dismiss_all)
            self.overlays.append(ov)

        # Synchronize tools and colors across all overlays
        if len(self.overlays) > 1:
            for src in self.overlays:
                for dst in self.overlays:
                    if src is not dst:
                        src.toolbar.tool_changed.connect(dst.canvas.set_tool)
                        src.toolbar.color_changed.connect(dst.canvas.set_color)
                        src.toolbar.stroke_changed.connect(lambda w, target=dst.canvas: target.set_stroke_width(w, emit_signal=False))
                        src.toolbar.clear_requested.connect(dst.canvas.clear_all)

        for ov in self.overlays:
            ov.show_on_screen(ov.target_screen)

    def setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        import os
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.png")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
        else:
            icon = QIcon(create_tray_icon_pixmap())

        self.tray = QSystemTrayIcon(icon, self.app)
        self.tray.setToolTip("Ghalam (قلم)")

        menu = QMenu()
        show_action = menu.addAction("Annotate Screen (Ghalam)")
        show_action.triggered.connect(self.show_overlays)

        menu.addSeparator()
        quit_action = menu.addAction("Exit")
        quit_action.triggered.connect(self.app.quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.is_any_overlay_visible():
                self.dismiss_all()
            else:
                self.show_overlays()

    def run(self, start_visible: bool = True):
        self.start_server()
        if self.is_daemon:
            self.setup_tray()

        if start_visible:
            self.show_overlays()

        return self.app.exec()
