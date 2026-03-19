"""Automation module — pastes screenshot into the target prompt and submits."""

import io
import time
import logging

import pyautogui
import win32clipboard
import win32gui
import win32con
from PIL import Image

import config
from monitor import get_paste_region

logger = logging.getLogger(__name__)

pyautogui.FAILSAFE = True  # move mouse to corner to abort
pyautogui.PAUSE = 0.05


def copy_image_to_clipboard_png(image: Image.Image):
    """Copy a PIL Image to the Windows clipboard as PNG data.

    Web apps (Gemini, ChatGPT) prefer PNG over raw BMP for image paste.
    """
    png_buf = io.BytesIO()
    image.convert("RGB").save(png_buf, "PNG")
    png_data = png_buf.getvalue()
    png_buf.close()

    CF_PNG = win32clipboard.RegisterClipboardFormat("PNG")

    bmp_buf = io.BytesIO()
    image.convert("RGB").save(bmp_buf, "BMP")
    bmp_data = bmp_buf.getvalue()[14:]
    bmp_buf.close()

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(CF_PNG, png_data)
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
    win32clipboard.CloseClipboard()

    logger.debug("Image copied to clipboard (PNG + DIB)")


def find_browser_window(title_keywords=None):
    """Find a browser window whose title contains any of the keywords.

    Returns the hwnd or None.
    """
    if title_keywords is None:
        title_keywords = config.BROWSER_TITLE_KEYWORDS

    result = []

    def enum_cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            for kw in title_keywords:
                if kw.lower() in title.lower():
                    result.append(hwnd)
                    return
    win32gui.EnumWindows(enum_cb, None)

    if result:
        logger.debug(f"Found browser window: hwnd={result[0]}, title={win32gui.GetWindowText(result[0])}")
        return result[0]
    logger.warning(f"No browser window found matching {title_keywords}")
    return None


def focus_browser_window():
    """Find and bring the target browser window to foreground, then click the prompt."""
    hwnd = find_browser_window()
    if hwnd:
        try:
            # Restore if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            # Bring to front
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.3)
            logger.debug("Browser window focused")
        except Exception as e:
            logger.warning(f"Could not focus browser: {e}")

    # Now click the prompt input area
    click_paste_area()
    time.sleep(0.3)
    # Click again to make sure cursor is in the text field
    click_paste_area()


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
    1. Copy screenshot to clipboard as PNG
    2. Focus the browser window and click the prompt
    3. Ctrl+V to paste
    4. Wait for image to render, then submit
    """
    logger.info("Starting paste-and-submit sequence")

    # Step 1: copy image to clipboard FIRST (before any window switching)
    copy_image_to_clipboard_png(screenshot)

    # Step 2: focus the browser and click the prompt input
    time.sleep(config.CLICK_DELAY)
    focus_browser_window()
    time.sleep(0.5)

    # Step 3: paste
    pyautogui.hotkey("ctrl", "v")
    logger.debug("Pasted from clipboard")

    # Step 4: wait for the image to render in the prompt
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
