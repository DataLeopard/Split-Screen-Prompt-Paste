"""Automation module — pastes screenshot into the target prompt and submits."""

import io
import os
import time
import logging
import struct
import tempfile

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

# Persistent temp directory for screenshots
_TEMP_DIR = os.path.join(tempfile.gettempdir(), "sspp_screenshots")
os.makedirs(_TEMP_DIR, exist_ok=True)


def save_screenshot_to_file(image: Image.Image) -> str:
    """Save screenshot as a PNG file and return the path."""
    path = os.path.join(_TEMP_DIR, "latest_capture.png")
    image.convert("RGB").save(path, "PNG")
    logger.debug(f"Screenshot saved to {path}")
    return path


def copy_image_to_clipboard_png(image: Image.Image):
    """Copy a PIL Image to the Windows clipboard as PNG + DIB."""
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


def click_attach_button():
    """Click the attach/upload (+) button in the paste zone."""
    x, y = _coords_in_paste_zone(config.ATTACH_BUTTON_X_RATIO, config.ATTACH_BUTTON_Y_RATIO)
    pyautogui.click(x, y)
    logger.debug(f"Clicked attach button at ({x}, {y})")


def paste_via_file_upload(screenshot: Image.Image):
    """Upload screenshot using Gemini's + button > Upload file > file dialog.

    Sequence:
    1. Save screenshot to temp file
    2. Focus browser
    3. Click the "+" attach button
    4. Click "Upload file" option in the popup menu
    5. Type the file path in the file dialog
    6. Press Enter to upload
    """
    filepath = save_screenshot_to_file(screenshot)
    logger.info(f"Screenshot saved: {filepath}")

    # Focus browser
    focus_browser_window()
    time.sleep(0.5)

    # Click the "+" attach button at bottom-left of Gemini input
    click_attach_button()
    logger.debug("Clicked attach button, waiting for menu...")
    time.sleep(1.0)

    # Click "Upload file" — it's typically the first option in the popup,
    # which appears just above the "+" button
    x, y = _coords_in_paste_zone(config.ATTACH_BUTTON_X_RATIO, config.ATTACH_BUTTON_Y_RATIO - 0.15)
    pyautogui.click(x, y)
    logger.debug(f"Clicked 'Upload file' option at ({x}, {y})")
    time.sleep(1.5)  # wait for file dialog to open

    # Now the Windows file dialog should be open
    # Type the full file path into the filename field
    # The filename field should already be focused
    pyautogui.hotkey("alt", "n")  # focus the "File name" field in Windows dialog
    time.sleep(0.3)
    # Clear any existing text
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    # Type the path (pyautogui.typewrite only handles ASCII, use pyperclip for paths)
    import pyperclip
    pyperclip.copy(filepath)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.3)
    pyautogui.press("enter")
    logger.debug("Submitted file path in dialog")
    time.sleep(2.0)  # wait for upload to complete

    logger.info("File uploaded via dialog")


def paste_via_clipboard(screenshot: Image.Image):
    """Paste screenshot via clipboard Ctrl+V."""
    copy_image_to_clipboard_png(screenshot)

    focus_browser_window()
    time.sleep(0.5)
    click_paste_area()
    time.sleep(0.5)
    click_paste_area()  # double-click to ensure focus
    time.sleep(0.3)

    pyautogui.hotkey("ctrl", "v")
    logger.debug("Pasted from clipboard via Ctrl+V")


def paste_and_submit(screenshot: Image.Image):
    """
    Full automation sequence:
    1. Attach/paste the screenshot
    2. Wait for it to load
    3. Submit
    """
    logger.info("Starting paste-and-submit sequence")

    paste_method = config.PASTE_METHOD

    if paste_method == "file_upload":
        paste_via_file_upload(screenshot)
    else:  # "clipboard"
        paste_via_clipboard(screenshot)

    # Wait for the image to render/upload in the prompt
    time.sleep(config.ENTER_DELAY)

    # Submit
    if config.SUBMIT_METHOD == "click_button":
        click_submit_button()
        logger.info("Submitted (clicked send button)")
    else:
        click_paste_area()
        time.sleep(0.3)
        pyautogui.press("enter")
        logger.info("Submitted (Enter pressed)")
