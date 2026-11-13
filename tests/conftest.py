"""
Shared pytest configuration.

Every test runs against Qt's offscreen platform so the suite works in CI and on a
headless machine. ``setdefault`` keeps an explicit ``QT_QPA_PLATFORM`` from being
overridden, which is what a developer uses to run against a real session.
"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
