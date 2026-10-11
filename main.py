"""Entry point. Run `python main.py`, or `python main.py --web` to test the UI in a browser."""

import argparse

from adb_toolkit.app import run


def main() -> None:
    parser = argparse.ArgumentParser(description="ADB Toolkit: adb and fastboot in one window.")
    parser.add_argument("--web", action="store_true", help="serve the UI to a browser instead of opening a window")
    parser.add_argument("--port", type=int, default=8550, help="port used with --web (default 8550)")
    args = parser.parse_args()
    run(web=args.web, port=args.port)


if __name__ == "__main__":
    main()
