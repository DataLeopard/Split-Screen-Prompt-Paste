"""Automation module — pastes screenshot into the target prompt and submits."""

import io
import time
import logging

import pyautogui
import win32clipboard
from PIL import Image

import config
from monitor import get_paste_region

logger = logging.getLogger(__name__)

pyautogui.FAILSAFE = True  # move mouse to corner to abort
pyautogui.PAUSE = 0.05


def copy_image_to_clipboard(image: Image.Image):
    """Copy a PIL Image to the Windows clipboard as a bitmap."""
    output = io.BytesIO()
    image.convert("RGB").save(output, "BMP")
    bmp_data = output.getvalue()[14:]  # strip BMP file header
    output.close()

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
    win32clipboard.CloseClipboard()
    logger.debug("Image copied to clipboard")


def click_paste_area():
    """Click on the prompt/input area on the paste side of the screen."""
    region = get_paste_region()
    x = region[0] + int((region[2] - region[0]) * config.PASTE_CLICK_X_RATIO)
    y = region[1] + int((region[3] - region[1]) * config.PASTE_CLICK_Y_RATIO)
    pyautogui.click(x, y)
    logger.debug(f"Clicked paste area at ({x}, {y})")


def paste_and_submit(screenshot: Image.Image):
    """
    Full automation sequence:
    1. Copy screenshot to clipboard
    2. Click the paste target area
    3. Ctrl+V to paste
    4. Enter to submit
    """
    logger.info("Starting paste-and-submit sequence")

    # Step 1: copy image to clipboard
    copy_image_to_clipboard(screenshot)

    # Step 2: click on the prompt area
    time.sleep(config.CLICK_DELAY)
    click_paste_area()

    # Step 3: paste
    time.sleep(config.CLICK_DELAY)
    pyautogui.hotkey("ctrl", "v")
    logger.debug("Pasted from clipboard")

    # Step 4: submit
    time.sleep(config.ENTER_DELAY)
    pyautogui.press("enter")
    logger.info("Submitted (Enter pressed)")
