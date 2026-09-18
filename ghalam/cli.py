"""
CLI entry point for Ghalam.
"""
import sys
import signal
import argparse
from ghalam.app import AnnotatorApp


def main():
    # Ensure Ctrl+C terminates immediately from terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    parser = argparse.ArgumentParser(description="Ghalam (قلم) - Screen Annotator")
    parser.add_argument("--daemon", action="store_true", help="Start in background daemon mode")
    parser.add_argument("--toggle", action="store_true", help="Toggle overlay display via IPC")
    parser.add_argument("--quit", action="store_true", help="Quit running daemon instance")
    parser.add_argument(
        "--monitor", 
        type=str, 
        default="active", 
        help="Target monitor: 'active' (auto-detect), 'all' (both screens), 'hdmi', 'dp', or index (0, 1)"
    )
    args = parser.parse_args()

    # If --quit requested
    if args.quit:
        if AnnotatorApp.send_ipc_command("QUIT"):
            print("Sent QUIT command to running instance.")
            sys.exit(0)
        else:
            print("No running instance found.")
            sys.exit(0)

    # If --toggle requested, try sending to existing daemon first
    cmd = "TOGGLE" if args.toggle else "SHOW"
    if AnnotatorApp.send_ipc_command(cmd):
        sys.exit(0)

    # No existing instance running, start new app
    app = AnnotatorApp(is_daemon=args.daemon, monitor_target=args.monitor)
    start_visible = not args.daemon
    sys.exit(app.run(start_visible=start_visible))


if __name__ == "__main__":
    main()
