"""
CLI entry point for Ghalam.
"""
import argparse
import signal
import sys

from ghalam import __version__
from ghalam.app import REPLY_ERROR, REPLY_MONITOR_IGNORED, AnnotatorApp


def main():
    # Ensure Ctrl+C terminates immediately from terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        prog="ghalam",
        description="Ghalam (قلم) - Fast, elegant screen drawing & annotation tool for Linux",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument("--daemon", action="store_true", help="Start in background daemon mode")
    parser.add_argument("--toggle", action="store_true", help="Toggle overlay display via IPC")
    parser.add_argument("--quit", action="store_true", help="Quit running daemon instance")
    parser.add_argument(
        "--monitor",
        type=str,
        default=None,
        help="Target monitor: 'active' (auto-detect), 'all' (both screens), 'hdmi', 'dp', or index (0, 1)"
    )
    args = parser.parse_args()

    # If --quit requested
    if args.quit:
        reply = AnnotatorApp.send_ipc_command("QUIT")
        if reply:
            print("Sent QUIT command to running instance.")
        else:
            print("No running instance found.")
        sys.exit(1 if reply == REPLY_ERROR else 0)

    # If --toggle requested, try sending to existing daemon first
    cmd = "TOGGLE" if args.toggle else "SHOW"
    payload = cmd if args.monitor is None else f"{cmd}:{args.monitor}"
    reply = AnnotatorApp.send_ipc_command(payload)
    if reply:
        if reply == REPLY_MONITOR_IGNORED:
            print(
                "note: --monitor ignored, an instance is already running",
                file=sys.stderr,
            )
        sys.exit(1 if reply == REPLY_ERROR else 0)

    # No existing instance running, start new app
    app = AnnotatorApp(is_daemon=args.daemon, monitor_target=args.monitor or "active")
    start_visible = not args.daemon
    sys.exit(app.run(start_visible=start_visible))


if __name__ == "__main__":
    main()
