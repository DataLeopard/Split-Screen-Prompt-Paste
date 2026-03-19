"""Quick test: screenshots left half, puts image on clipboard via .NET, pastes into Gemini.

Run: python test_paste.py
You get 5 seconds to arrange windows.
"""

import time
import subprocess
import os
import tempfile

import pyautogui
import win32gui
import win32con
from PIL import ImageGrab

pyautogui.FAILSAFE = True

TEMP_IMG = os.path.join(tempfile.gettempdir(), "sspp_screenshots", "test_capture.png")
os.makedirs(os.path.dirname(TEMP_IMG), exist_ok=True)


def main():
    import ctypes
    u = ctypes.windll.user32
    u.SetProcessDPIAware()
    sw, sh = u.GetSystemMetrics(0), u.GetSystemMetrics(1)

    print(f"Screen: {sw}x{sh}")
    input("\nArrange windows, then press Enter to start 5s countdown...")

    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    # 1. Screenshot left half
    print("\n[1] Screenshotting left half...")
    img = ImageGrab.grab(bbox=(0, 0, sw // 2, sh))
    img.save(TEMP_IMG, "PNG")
    print(f"    Saved: {TEMP_IMG}")

    # 2. Copy to clipboard via .NET (same as Windows Snipping Tool)
    print("[2] Copying image to clipboard via PowerShell/.NET...")
    ps = (
        f'Add-Type -Assembly System.Windows.Forms; '
        f'Add-Type -Assembly System.Drawing; '
        f'$img = [System.Drawing.Image]::FromFile("{TEMP_IMG}"); '
        f'[System.Windows.Forms.Clipboard]::SetImage($img); '
        f'$img.Dispose()'
    )
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        print(f"    ERROR: {r.stderr}")
        return
    print("    OK — clipboard now has image (same format as Snipping Tool)")

    # 3. Find Gemini
    print("[3] Finding Gemini window...")
    found = []
    def cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            t = win32gui.GetWindowText(hwnd)
            if "gemini" in t.lower():
                found.append((hwnd, t))
    win32gui.EnumWindows(cb, None)
    if not found:
        print("    NOT FOUND! Make sure Gemini tab is open.")
        return
    hwnd, title = found[0]
    print(f"    Found: '{title}'")

    # 4. Focus
    print("[4] Focusing...")
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.5)

    # 5. Click Gemini input
    click_x = sw // 2 + (sw // 2) // 2  # center of right half
    click_y = int(sh * 0.89)  # near bottom where "Ask Gemini" box is
    print(f"[5] Clicking Gemini input at ({click_x}, {click_y})...")
    pyautogui.click(click_x, click_y)
    time.sleep(0.5)

    # 6. Ctrl+V
    print("[6] Ctrl+V...")
    pyautogui.hotkey("ctrl", "v")
    time.sleep(3)

    # 7. Enter
    print("[7] Enter...")
    pyautogui.press("enter")

    print("\nDONE! Check Gemini — did the IMAGE appear (not a file path)?")


if __name__ == "__main__":
    main()
