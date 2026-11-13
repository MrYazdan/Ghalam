"""
IPC semantics: wire format, dispatch table and socket ownership.

The socket tests drive the real QLocalServer through the event loop, so they cover
the code path a second ``ghalam`` invocation takes.
"""
import pytest
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

from ghalam.app import (
    REPLY_ERROR,
    REPLY_MONITOR_IGNORED,
    REPLY_OK,
    AnnotatorApp,
    parse_ipc_command,
)

pytestmark = pytest.mark.gui


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("SHOW", ("SHOW", None)),
        ("  show:HDMI \n", ("SHOW", "HDMI")),
        ("SHOW:", ("SHOW", None)),
        ("FOO:all", ("FOO", "all")),
        ("", ("", None)),
    ],
)
def test_parse_ipc_command(raw, expected):
    assert parse_ipc_command(raw) == expected


@pytest.fixture
def app(qapp):
    return AnnotatorApp(is_daemon=True)


def _visibility(app, monkeypatch, visible: bool):
    monkeypatch.setattr(app, "is_any_overlay_visible", lambda: visible)


def test_show_raises_a_visible_overlay_without_dismissing(app, monkeypatch):
    calls = []
    _visibility(app, monkeypatch, True)
    monkeypatch.setattr(app, "raise_overlays", lambda: calls.append("raise"))
    monkeypatch.setattr(app, "dismiss_all", lambda: calls.append("dismiss"))

    assert app.handle_command("SHOW") == REPLY_OK
    assert calls == ["raise"]


def test_show_builds_when_hidden(app, monkeypatch):
    calls = []
    _visibility(app, monkeypatch, False)
    monkeypatch.setattr(app, "show_overlays", lambda: calls.append("show"))

    assert app.handle_command("SHOW") == REPLY_OK
    assert calls == ["show"]


def test_toggle_hides_when_visible(app, monkeypatch):
    calls = []
    _visibility(app, monkeypatch, True)
    monkeypatch.setattr(app, "dismiss_all", lambda: calls.append("dismiss"))

    assert app.handle_command("TOGGLE") == REPLY_OK
    assert calls == ["dismiss"]


def test_toggle_builds_when_hidden(app, monkeypatch):
    calls = []
    _visibility(app, monkeypatch, False)
    monkeypatch.setattr(app, "show_overlays", lambda: calls.append("show"))

    assert app.handle_command("TOGGLE") == REPLY_OK
    assert calls == ["show"]


def test_show_with_a_new_target_sets_the_monitor(app, monkeypatch):
    shown = []
    _visibility(app, monkeypatch, False)
    monkeypatch.setattr(app, "show_overlays", lambda: shown.append(app.monitor_target))

    assert app.handle_command("SHOW", "hdmi") == REPLY_OK
    assert app.monitor_target == "hdmi"
    assert shown == ["hdmi"]


def test_show_with_a_matching_target_keeps_the_overlay(app, monkeypatch):
    app.monitor_target = "all"
    calls = []
    _visibility(app, monkeypatch, True)
    monkeypatch.setattr(app, "raise_overlays", lambda: calls.append("raise"))

    assert app.handle_command("SHOW", "ALL") == REPLY_OK
    assert calls == ["raise"]


def test_show_with_another_target_on_a_visible_overlay_is_reported(app, monkeypatch):
    app.monitor_target = "active"
    calls = []
    _visibility(app, monkeypatch, True)
    monkeypatch.setattr(app, "raise_overlays", lambda: calls.append("raise"))

    assert app.handle_command("SHOW", "all") == REPLY_MONITOR_IGNORED
    assert calls == ["raise"]


def test_quit_requests_application_exit(app, monkeypatch):
    calls = []
    monkeypatch.setattr(app.app, "quit", lambda: calls.append(True))

    assert app.handle_command("QUIT") == REPLY_OK
    assert calls == [True]


def test_unknown_command_is_an_error(app):
    assert app.handle_command("NOPE") == REPLY_ERROR


@pytest.fixture
def socket_name(monkeypatch):
    name = "ghalam_test_ipc"
    monkeypatch.setattr("ghalam.app.SOCKET_NAME", name)
    yield name
    QLocalServer.removeServer(name)


def _connect(name: str) -> QLocalSocket:
    client = QLocalSocket()
    client.connectToServer(name)
    assert client.waitForConnected(1000)
    return client


def test_socket_round_trip(qapp, qtbot, socket_name, monkeypatch):
    app = AnnotatorApp(is_daemon=True)
    calls = []
    _visibility(app, monkeypatch, False)
    monkeypatch.setattr(app, "show_overlays", lambda: calls.append("show"))
    assert app.start_server() is True
    try:
        client = _connect(socket_name)
        client.write(b"SHOW")
        assert client.waitForBytesWritten(1000)

        qtbot.waitUntil(lambda: calls == ["show"], timeout=1000)
        qtbot.waitUntil(lambda: client.bytesAvailable() >= len(REPLY_OK), timeout=1000)
        assert bytes(client.readAll()).decode() == REPLY_OK
    finally:
        app.server.close()


def test_second_instance_does_not_steal_the_socket(qapp, qtbot, socket_name, monkeypatch):
    first = AnnotatorApp(is_daemon=True)
    calls = []
    _visibility(first, monkeypatch, False)
    monkeypatch.setattr(first, "show_overlays", lambda: calls.append("show"))
    assert first.start_server() is True

    second = AnnotatorApp(is_daemon=True)
    try:
        assert second.start_server() is False

        client = _connect(socket_name)
        client.write(b"SHOW")
        assert client.waitForBytesWritten(1000)
        qtbot.waitUntil(lambda: calls == ["show"], timeout=1000)
        qtbot.waitUntil(lambda: client.bytesAvailable() >= len(REPLY_OK), timeout=1000)
        assert bytes(client.readAll()).decode() == REPLY_OK
    finally:
        first.server.close()


def test_stale_socket_file_is_replaced(qapp, socket_name):
    probe = QLocalServer()
    assert probe.listen(socket_name)
    path = probe.fullServerName()
    probe.close()
    open(path, "w").close()

    app = AnnotatorApp(is_daemon=True)
    try:
        assert app.start_server() is True
    finally:
        app.server.close()


def test_legacy_client_disconnect_is_safe(qapp, qtbot, socket_name, monkeypatch):
    app = AnnotatorApp(is_daemon=True)
    handled = []
    monkeypatch.setattr(
        app,
        "handle_command",
        lambda command, target=None: handled.append(command) or REPLY_OK,
    )
    assert app.start_server() is True
    try:
        client = _connect(socket_name)
        client.write(b"SHOW")
        assert client.waitForBytesWritten(1000)
        client.disconnectFromServer()

        qtbot.waitUntil(lambda: handled == ["SHOW"], timeout=1000)
    finally:
        app.server.close()
