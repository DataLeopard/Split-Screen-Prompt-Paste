"""Calibration tool — shows where clicks will land with a visible red dot.

Run this to verify your config.py coordinates are correct.
Press Ctrl+C to exit.
"""

import time
import pyautogui
import config
from monitor import get_paste_region, get_screen_size

pyautogui.FAILSAFE = True


def show_coordinates():
    sw, sh = get_screen_size()
    region = get_paste_region()

    print(f"Screen size: {sw}x{sh}")
    print(f"Paste zone:  {region}")
    print()

    # Calculate all click targets
    def coords(xr, yr):
        x = region[0] + int((region[2] - region[0]) * xr)
        y = region[1] + int((region[3] - region[1]) * yr)
        return x, y

    input_pos = coords(config.PASTE_CLICK_X_RATIO, config.PASTE_CLICK_Y_RATIO)
    submit_pos = coords(config.SUBMIT_BUTTON_X_RATIO, config.SUBMIT_BUTTON_Y_RATIO)

    print(f"Input click:  {input_pos}  (PASTE_CLICK ratios: {config.PASTE_CLICK_X_RATIO}, {config.PASTE_CLICK_Y_RATIO})")
    print(f"Submit click: {submit_pos}  (SUBMIT_BUTTON ratios: {config.SUBMIT_BUTTON_X_RATIO}, {config.SUBMIT_BUTTON_Y_RATIO})")

    if hasattr(config, 'ATTACH_BUTTON_X_RATIO'):
        attach_pos = coords(config.ATTACH_BUTTON_X_RATIO, config.ATTACH_BUTTON_Y_RATIO)
        print(f"Attach click: {attach_pos}  (ATTACH_BUTTON ratios: {config.ATTACH_BUTTON_X_RATIO}, {config.ATTACH_BUTTON_Y_RATIO})")

    print()
    print("Moving mouse to each position for 3 seconds each...")
    print("Watch where the cursor goes!")
    print()

    positions = [
        ("INPUT (where image will be pasted)", input_pos),
        ("SUBMIT BUTTON (where send is clicked)", submit_pos),
    ]

    for name, (x, y) in positions:
        print(f"  >> {name} at ({x}, {y}) ...")
        pyautogui.moveTo(x, y, duration=0.5)
        time.sleep(3)

    print()
    print("Done! If the cursor didn't land on the right spots, adjust the")
    print("ratios in config.py and run this again.")
    print()
    print("TIP: To find the right ratio for any pixel:")
    print(f"  X ratio = (pixel_x - {region[0]}) / {region[2] - region[0]}")
    print(f"  Y ratio = (pixel_y - {region[1]}) / {region[3] - region[1]}")


if __name__ == "__main__":
    print("=== SSPP Coordinate Calibrator ===")
    print("Arrange your windows first, then press Enter to start.")
    input()
    show_coordinates()
