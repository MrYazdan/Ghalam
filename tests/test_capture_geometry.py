"""Capture geometry: crop math, screen mapping, tool precedence and command builders."""
from PyQt6.QtCore import QRect, QSize

from ghalam.capture import (
    crop_rect_for_screen,
    full_command,
    image_rect_for_screen,
    output_command,
    pick_tool,
    whole_desktop_command,
)


def test_crop_keeps_a_contained_rect():
    assert crop_rect_for_screen(QRect(0, 0, 1920, 1080), QSize(3840, 1080)) == QRect(0, 0, 1920, 1080)


def test_crop_takes_the_right_half_of_a_wide_image():
    assert crop_rect_for_screen(QRect(1920, 0, 1920, 1080), QSize(3840, 1080)) == QRect(1920, 0, 1920, 1080)


def test_crop_clamps_a_partly_visible_rect():
    assert crop_rect_for_screen(QRect(1800, 0, 400, 1080), QSize(1920, 1080)) == QRect(1800, 0, 120, 1080)


def test_crop_clips_a_negative_origin():
    assert crop_rect_for_screen(QRect(-100, 0, 200, 100), QSize(1920, 1080)) == QRect(0, 0, 100, 100)


def test_crop_rejects_a_rect_outside_the_image():
    assert crop_rect_for_screen(QRect(2000, 0, 400, 1080), QSize(1920, 1080)).isEmpty()


def test_mapping_handles_a_negative_origin():
    union = QRect(-1920, 0, 3840, 1080)
    assert image_rect_for_screen(QRect(0, 0, 1920, 1080), union, QSize(3840, 1080)) == QRect(
        1920, 0, 1920, 1080
    )


def test_mapping_scales_device_pixels():
    union = QRect(0, 0, 3840, 1080)
    assert image_rect_for_screen(QRect(1920, 0, 1920, 1080), union, QSize(4800, 1350)) == QRect(
        2400, 0, 2400, 1350
    )


def test_mapping_rejects_an_empty_union():
    assert image_rect_for_screen(QRect(0, 0, 100, 100), QRect(), QSize(100, 100)).isEmpty()


def test_pick_tool_follows_precedence():
    installed = {"spectacle", "gnome-screenshot"}
    assert pick_tool(lambda name: name if name in installed else None) == "spectacle"
    assert pick_tool(lambda name: None) is None


def test_command_builders():
    assert output_command("DP-1", "/tmp/a.png") == ["grim", "-o", "DP-1", "/tmp/a.png"]
    assert full_command("/tmp/a.png") == ["spectacle", "-b", "-n", "-f", "-o", "/tmp/a.png"]
    assert whole_desktop_command("/tmp/a.png") == ["grim", "/tmp/a.png"]
