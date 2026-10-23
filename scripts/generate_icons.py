"""
Generates the multi-size hicolor icon set from assets/icon.png.

Run with: uv run python scripts/generate_icons.py

The output lives in assets/icons/ and is committed, so packaging never has to
depend on the Qt image plugins at build time.
"""
import os
import shutil
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage

SIZES = (16, 24, 32, 48, 64, 128, 256, 512)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "assets", "icon.png")
TARGET_DIR = os.path.join(ROOT, "assets", "icons")


def main() -> int:
    source = QImage(SOURCE)
    if source.isNull():
        print(f"cannot read {SOURCE}", file=sys.stderr)
        return 1

    os.makedirs(TARGET_DIR, exist_ok=True)
    for size in SIZES:
        target = os.path.join(TARGET_DIR, f"ghalam-{size}.png")
        if size >= source.width():
            # Keep the 512px entry byte-identical to assets/icon.png: git stores one blob
            # for both files, so the largest icon costs no extra repository space.
            shutil.copyfile(SOURCE, target)
        else:
            scaled = source.scaled(
                size,
                size,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            if not scaled.save(target, "PNG"):
                print(f"cannot write {target}", file=sys.stderr)
                return 1
        print(f"{size:>4}px  {os.path.getsize(target) / 1024:6.1f} KB  {target}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
