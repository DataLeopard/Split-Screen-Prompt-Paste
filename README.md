# Split Screen Prompt Paste

Monitors one half of your screen for visual changes. When a change is detected (e.g. you click Submit on a form), it automatically screenshots the changed content, pastes it into a prompt on the other half of the screen, and presses Enter to search.

## Quick Start

```
1. Run setup.bat          (installs dependencies)
2. Double-click start.bat (launches the app)
3. Press Ctrl+Shift+F9    (start monitoring)
4. Press Ctrl+Shift+F9    (pause monitoring)
5. Press Ctrl+Shift+F10   (quit)
```

Or run directly:
```bash
python app.py
```

## How It Works

1. **Polls the left half** of your screen every 0.5 seconds
2. **Detects visual changes** using pixel-level comparison (NumPy)
3. **Screenshots** the changed left side
4. **Clicks** the prompt area on the right side
5. **Pastes** the screenshot via clipboard (Ctrl+V)
6. **Presses Enter** to submit/search
7. **Cools down** for 3 seconds to avoid re-triggering

## Controls

| Action | Method |
|---|---|
| Start / Pause | `Ctrl+Shift+F9` or system tray → Toggle |
| Quit | `Ctrl+Shift+F10` or system tray → Quit |
| Emergency stop | Move mouse to any screen corner (pyautogui failsafe) |
| Force kill | Double-click `stop.bat` |

## Configuration

Edit `config.py` to adjust:

- `MONITOR_SIDE` / `PASTE_SIDE` — which half to watch vs. paste into
- `POLL_INTERVAL` — how often to check for changes (seconds)
- `CHANGE_PERCENT` — sensitivity threshold (lower = more sensitive)
- `COOLDOWN` — seconds to wait after a paste before monitoring resumes
- `PASTE_CLICK_X_RATIO` / `PASTE_CLICK_Y_RATIO` — where to click on the paste side
- `TOGGLE_HOTKEY` / `QUIT_HOTKEY` — keyboard shortcuts

## Requirements

- Windows 10/11
- Python 3.10+
- Dependencies: `pip install -r requirements.txt`

## Running Tests

```bash
python -m pytest tests/ -v
```
