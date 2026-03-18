"""
Split Screen Prompt Paste — Main Application

Monitors one half of the screen for changes, screenshots it,
pastes into the other half's prompt, and hits Enter.

Controls:
  Ctrl+Shift+F9  — Toggle monitoring on/off
  Ctrl+Shift+F10 — Quit
  System tray icon — Right-click for menu
"""

import sys
import time
import threading
import logging
from pathlib import Path

import keyboard
import pystray
from PIL import Image, ImageDraw

import config
from monitor import get_monitor_region, capture_region, images_differ
from automation import paste_and_submit

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("app")

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
monitoring = threading.Event()
quitting = threading.Event()


# ---------------------------------------------------------------------------
# Core loop
# ---------------------------------------------------------------------------
def monitor_loop():
    """Main monitoring loop — runs in its own thread."""
    logger.info("Monitor thread started")
    region = get_monitor_region()
    logger.info(f"Monitoring region: {region}")

    previous_frame = None

    while not quitting.is_set():
        if not monitoring.is_set():
            time.sleep(0.2)
            continue

        current_frame = capture_region(region)

        if images_differ(previous_frame, current_frame):
            if previous_frame is not None:  # skip the very first frame
                logger.info("Change detected — capturing and pasting")
                try:
                    paste_and_submit(current_frame)
                except Exception:
                    logger.exception("Error during paste-and-submit")
                # cooldown to avoid rapid re-triggers
                logger.debug(f"Cooldown {config.COOLDOWN}s")
                time.sleep(config.COOLDOWN)
                # re-capture after cooldown so we don't immediately re-trigger
                current_frame = capture_region(region)

            previous_frame = current_frame
        else:
            previous_frame = current_frame

        time.sleep(config.POLL_INTERVAL)

    logger.info("Monitor thread exiting")


# ---------------------------------------------------------------------------
# Hotkeys
# ---------------------------------------------------------------------------
def toggle_monitoring():
    if monitoring.is_set():
        monitoring.clear()
        logger.info("⏸  Monitoring PAUSED")
        update_tray_icon()
    else:
        monitoring.set()
        logger.info("▶  Monitoring ACTIVE")
        update_tray_icon()


def quit_app():
    logger.info("Quit requested")
    monitoring.clear()
    quitting.set()
    if tray_icon:
        tray_icon.stop()


# ---------------------------------------------------------------------------
# System tray
# ---------------------------------------------------------------------------
tray_icon = None


def create_icon_image(active: bool) -> Image.Image:
    """Generate a simple coloured icon: green=active, grey=paused."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    colour = (0, 200, 80, 255) if active else (140, 140, 140, 255)
    draw.ellipse([4, 4, size - 4, size - 4], fill=colour)
    # Small "S" in centre
    draw.text((size // 2 - 6, size // 2 - 10), "S", fill=(255, 255, 255, 255))
    return img


def update_tray_icon():
    if tray_icon:
        tray_icon.icon = create_icon_image(monitoring.is_set())
        status = "Active" if monitoring.is_set() else "Paused"
        tray_icon.title = f"Split Screen Prompt Paste — {status}"


def build_tray():
    global tray_icon

    def on_toggle(icon, item):
        toggle_monitoring()

    def on_quit(icon, item):
        quit_app()

    menu = pystray.Menu(
        pystray.MenuItem("Toggle Monitoring (Ctrl+Shift+F9)", on_toggle, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit (Ctrl+Shift+F10)", on_quit),
    )

    tray_icon = pystray.Icon(
        "split_screen_prompt_paste",
        create_icon_image(False),
        "Split Screen Prompt Paste — Paused",
        menu,
    )
    return tray_icon


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    logger.info("=" * 50)
    logger.info("Split Screen Prompt Paste starting")
    logger.info(f"Toggle hotkey : {config.TOGGLE_HOTKEY}")
    logger.info(f"Quit hotkey   : {config.QUIT_HOTKEY}")
    logger.info("=" * 50)

    # Register global hotkeys
    keyboard.add_hotkey(config.TOGGLE_HOTKEY, toggle_monitoring, suppress=True)
    keyboard.add_hotkey(config.QUIT_HOTKEY, quit_app, suppress=True)

    # Start monitor thread
    thread = threading.Thread(target=monitor_loop, daemon=True)
    thread.start()

    # Build and run system tray (blocks on this thread)
    icon = build_tray()

    print("\n  Split Screen Prompt Paste is running.")
    print(f"  Ctrl+Shift+F9  = Start / Pause monitoring")
    print(f"  Ctrl+Shift+F10 = Quit")
    print("  (also available from system tray icon)\n")

    try:
        icon.run()
    except KeyboardInterrupt:
        pass
    finally:
        quit_app()
        thread.join(timeout=2)
        keyboard.unhook_all()
        logger.info("Application stopped.")


if __name__ == "__main__":
    main()
