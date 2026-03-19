"""Screen change detection module."""

import ctypes
import numpy as np
from PIL import ImageGrab
import config


def get_screen_size():
    """Return (width, height) of the primary monitor."""
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def get_monitor_region():
    """Return the (left, top, right, bottom) bounding box for the monitored half."""
    screen_w, screen_h = get_screen_size()

    if config.MONITOR_SIDE == "left":
        return (0, 0, screen_w // 2, screen_h)
    else:
        return (screen_w // 2, 0, screen_w, screen_h)


def get_paste_region():
    """Return the (left, top, right, bottom) bounding box for the paste zone."""
    screen_w, screen_h = get_screen_size()

    if config.PASTE_ZONE == "bottom_right":
        top = int(screen_h * config.PASTE_ZONE_TOP_RATIO)
        return (screen_w // 2, top, screen_w, screen_h)
    elif config.PASTE_ZONE == "bottom_left":
        top = int(screen_h * config.PASTE_ZONE_TOP_RATIO)
        return (0, top, screen_w // 2, screen_h)
    elif config.PASTE_ZONE == "right":
        return (screen_w // 2, 0, screen_w, screen_h)
    else:  # "left"
        return (0, 0, screen_w // 2, screen_h)


def capture_region(region):
    """Capture a screenshot of the given region. Returns a PIL Image."""
    return ImageGrab.grab(bbox=region)


def images_differ(img1, img2):
    """Compare two PIL images. Returns True if they differ beyond threshold."""
    if img1 is None or img2 is None:
        return True
    if img1.size != img2.size:
        return True

    arr1 = np.array(img1.convert("RGB"))
    arr2 = np.array(img2.convert("RGB"))

    diff = np.abs(arr1.astype(int) - arr2.astype(int))
    changed_pixels = np.any(diff > config.PIXEL_THRESHOLD, axis=2)
    change_ratio = np.mean(changed_pixels)

    return change_ratio >= config.CHANGE_PERCENT
