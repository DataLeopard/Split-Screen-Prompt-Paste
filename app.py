"""
Split Screen Prompt Paste — Main Application

Monitors one half of the screen for changes, screenshots it,
pastes into the other half's prompt, and submits.

Controls:
  Ctrl+Shift+F9  — Toggle monitoring on/off (with countdown)
  Ctrl+Shift+F10 — Quit
  System tray icon — Right-click for menu
"""

import sys
import time
import threading
import logging

import keyboard
import pystray
from PIL import Image, ImageDraw

import config
from monitor import get_monitor_region, capture_region, images_differ
from automation import paste_and_submit
from overlay import StatusOverlay

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
overlay = None


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
            previous_frame = None
            time.sleep(0.2)
            continue

        current_frame = capture_region(region)

        if images_differ(previous_frame, current_frame):
            if previous_frame is not None:  # skip the very first frame
                logger.info("Change detected — capturing and pasting")
                if overlay:
                    overlay.update("SSPP: PASTING...", "#ff9900")
                try:
                    paste_and_submit(current_frame)
                except Exception:
                    logger.exception("Error during paste-and-submit")
                # cooldown to avoid rapid re-triggers
                logger.debug(f"Cooldown {config.COOLDOWN}s")
                if overlay:
                    overlay.update(f"SSPP: COOLDOWN {config.COOLDOWN}s", "#ffcc00")
                time.sleep(config.COOLDOWN)
                # re-capture after cooldown so we don't immediately re-trigger
                current_frame = capture_region(region)
                if overlay and monitoring.is_set():
                    overlay.update("SSPP: MONITORING", "#00cc55")

            previous_frame = current_frame
        else:
            previous_frame = current_frame

        time.sleep(config.POLL_INTERVAL)

    logger.info("Monitor thread exiting")


# ---------------------------------------------------------------------------
# Countdown & toggle
# ---------------------------------------------------------------------------
def countdown_and_start():
    """Run a visible countdown, then activate monitoring."""
    delay = config.STARTUP_DELAY
    logger.info(f"Countdown: {delay}s before monitoring starts")

    for i in range(delay, 0, -1):
        if quitting.is_set():
            return
        if overlay:
            overlay.update(f"SSPP: STARTING IN {i}...", "#ff5555")
        logger.info(f"  Starting in {i}...")
        time.sleep(1)

    if not quitting.is_set():
        monitoring.set()
        logger.info("Monitoring ACTIVE")
        if overlay:
            overlay.update("SSPP: MONITORING", "#00cc55")
        update_tray_icon()


def toggle_monitoring():
    if monitoring.is_set():
        monitoring.clear()
        logger.info("Monitoring PAUSED")
        if overlay:
            overlay.update("SSPP: PAUSED", "#888888")
        update_tray_icon()
    else:
        # Start countdown in a separate thread so hotkeys stay responsive
        threading.Thread(target=countdown_and_start, daemon=True).start()


def quit_app():
    logger.info("Quit requested")
    monitoring.clear()
    quitting.set()
    if overlay:
        overlay.update("SSPP: STOPPING...", "#ff3333")
        time.sleep(0.3)
        overlay.destroy()
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
    global overlay

    logger.info("=" * 50)
    logger.info("Split Screen Prompt Paste starting")
    logger.info(f"Toggle hotkey  : {config.TOGGLE_HOTKEY}")
    logger.info(f"Quit hotkey    : {config.QUIT_HOTKEY}")
    logger.info(f"Startup delay  : {config.STARTUP_DELAY}s")
    logger.info(f"Paste zone     : {config.PASTE_ZONE}")
    logger.info(f"Submit method  : {config.SUBMIT_METHOD}")
    logger.info("=" * 50)

    # Create overlay
    overlay = StatusOverlay()
    overlay.update("SSPP: PAUSED", "#888888")

    # Register global hotkeys
    keyboard.add_hotkey(config.TOGGLE_HOTKEY, toggle_monitoring, suppress=True)
    keyboard.add_hotkey(config.QUIT_HOTKEY, quit_app, suppress=True)

    # Start monitor thread
    thread = threading.Thread(target=monitor_loop, daemon=True)
    thread.start()

    # Build and run system tray (blocks on this thread)
    icon = build_tray()

    print("\n  Split Screen Prompt Paste is running.")
    print(f"  Ctrl+Shift+F9  = Start / Pause (with {config.STARTUP_DELAY}s countdown)")
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
