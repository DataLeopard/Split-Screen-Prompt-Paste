"""Automation module — pastes screenshot into the target prompt and submits."""

import os
import time
import logging
import subprocess
import tempfile

import pyautogui
import win32gui
import win32con
from PIL import Image

import config
from monitor import get_paste_region

logger = logging.getLogger(__name__)

pyautogui.FAILSAFE = True  # move mouse to corner to abort
pyautogui.PAUSE = 0.05

# Persistent temp directory for screenshots
_TEMP_DIR = os.path.join(tempfile.gettempdir(), "sspp_screenshots")
os.makedirs(_TEMP_DIR, exist_ok=True)
_SCREENSHOT_PATH = os.path.join(_TEMP_DIR, "latest_capture.png")


def copy_image_to_clipboard(image: Image.Image):
    """Copy a PIL Image to clipboard using .NET via PowerShell.

    This sets the clipboard in the same format as Windows Snipping Tool,
    which Chrome/Gemini/ChatGPT all accept for Ctrl+V image paste.
    """
    # Save to temp file first
    image.convert("RGB").save(_SCREENSHOT_PATH, "PNG")

    # Use PowerShell + .NET to set clipboard (same as Snipping Tool)
    # Uses $args[0] to avoid PowerShell injection via file path
    ps_cmd = (
        'Add-Type -Assembly System.Windows.Forms; '
        'Add-Type -Assembly System.Drawing; '
        '$img = [System.Drawing.Image]::FromFile($args[0]); '
        '[System.Windows.Forms.Clipboard]::SetImage($img); '
        '$img.Dispose()'
    )

    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_cmd, _SCREENSHOT_PATH],
        capture_output=True, text=True, timeout=10
    )

    if result.returncode != 0:
        logger.error(f"PowerShell clipboard failed: {result.stderr}")
    else:
        logger.debug("Image copied to clipboard via .NET (same as Snipping Tool)")


def find_browser_window(title_keywords=None):
    """Find a browser window whose title contains any of the keywords."""
    if title_keywords is None:
        title_keywords = config.BROWSER_TITLE_KEYWORDS

    result = []

    def enum_cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            for kw in title_keywords:
                if kw.lower() in title.lower():
                    result.append((hwnd, title))
                    return
    win32gui.EnumWindows(enum_cb, None)

    if result:
        hwnd, title = result[0]
        logger.debug(f"Found browser window: hwnd={hwnd}, title='{title}'")
        return hwnd
    logger.warning(f"No browser window found matching {title_keywords}")
    return None


def focus_browser_window():
    """Find and bring the target browser window to foreground."""
    hwnd = find_browser_window()
    if hwnd:
        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.5)
            logger.debug("Browser window focused")
            return True
        except Exception as e:
            logger.warning(f"Could not focus browser: {e}")
    return False


def _coords_in_paste_zone(x_ratio, y_ratio):
    """Convert relative ratios to absolute screen coordinates within the paste zone."""
    region = get_paste_region()
    x = region[0] + int((region[2] - region[0]) * x_ratio)
    y = region[1] + int((region[3] - region[1]) * y_ratio)
    return x, y


def click_paste_area():
    """Click on the prompt/input area in the paste zone."""
    x, y = _coords_in_paste_zone(config.PASTE_CLICK_X_RATIO, config.PASTE_CLICK_Y_RATIO)
    pyautogui.click(x, y)
    logger.debug(f"Clicked paste area at ({x}, {y})")


def click_submit_button():
    """Click the Send/Submit button in the paste zone."""
    x, y = _coords_in_paste_zone(config.SUBMIT_BUTTON_X_RATIO, config.SUBMIT_BUTTON_Y_RATIO)
    pyautogui.click(x, y)
    logger.debug(f"Clicked submit button at ({x}, {y})")


def paste_and_submit(screenshot: Image.Image):
    """
    Full automation sequence:
    1. Copy screenshot to clipboard via .NET (like Snipping Tool)
    2. Focus the browser and click the prompt
    3. Ctrl+V to paste the image
    4. Wait, then submit

    Returns True on success, False on failure.
    """
    logger.info("Starting paste-and-submit sequence")

    try:
        # Step 1: copy image to clipboard (via PowerShell/.NET)
        copy_image_to_clipboard(screenshot)

        # Step 2: focus browser and click prompt
        time.sleep(config.CLICK_DELAY)
        if not focus_browser_window():
            logger.error("Failed to focus browser window")
            return False
        time.sleep(0.3)
        click_paste_area()
        time.sleep(0.5)

        # Step 3: Ctrl+V paste
        pyautogui.hotkey("ctrl", "v")
        logger.debug("Pressed Ctrl+V")

        # Step 4: wait for image to render
        time.sleep(config.ENTER_DELAY)

        # Step 5: submit
        if config.SUBMIT_METHOD == "click_button":
            click_submit_button()
            logger.info("Submitted (clicked send button)")
        else:
            click_paste_area()
            time.sleep(0.3)
            pyautogui.press("enter")
            logger.info("Submitted (Enter pressed)")
        return True
    except Exception as e:
        logger.error(f"Automation sequence failed: {e}")
        return False
