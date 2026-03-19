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
    1. Copy screenshot to clipboard
    2. Click the paste target area
    3. Ctrl+V to paste
    4. Wait for image to render, then submit
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

    # Step 4: wait for the image to render in the prompt
    time.sleep(config.ENTER_DELAY)

    # Step 5: submit
    if config.SUBMIT_METHOD == "click_button":
        click_submit_button()
        logger.info("Submitted (clicked send button)")
    else:
        # Re-click input to ensure focus, then press Enter
        click_paste_area()
        time.sleep(0.3)
        pyautogui.press("enter")
        logger.info("Submitted (Enter pressed)")
