"""Configuration for Split Screen Prompt Paste."""

# --- Screen Layout ---
# Which half of the screen to monitor for changes
MONITOR_SIDE = "left"  # "left" or "right"

# Which half to paste the screenshot into
PASTE_SIDE = "right"  # "left" or "right"

# --- Change Detection ---
# How often to check for screen changes (seconds)
POLL_INTERVAL = 0.5

# Pixel difference threshold to count as a "change" (0-255)
PIXEL_THRESHOLD = 30

# Percentage of pixels that must differ to trigger capture (0.0-1.0)
CHANGE_PERCENT = 0.02  # 2% of pixels must change

# Cooldown after a paste before monitoring resumes (seconds)
COOLDOWN = 3.0

# --- Automation ---
# Delay before clicking the paste target (seconds)
CLICK_DELAY = 0.3

# Delay after pasting before hitting Enter (seconds)
ENTER_DELAY = 0.5

# Where to click on the paste side (relative to that half)
# (0.5, 0.9) = center horizontally, 90% down vertically (typical prompt box)
PASTE_CLICK_X_RATIO = 0.5
PASTE_CLICK_Y_RATIO = 0.9

# --- Hotkeys ---
TOGGLE_HOTKEY = "ctrl+shift+f9"
QUIT_HOTKEY = "ctrl+shift+f10"

# --- Logging ---
LOG_FILE = "split_screen.log"
LOG_LEVEL = "INFO"
