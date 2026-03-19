"""Configuration for Split Screen Prompt Paste."""

# --- Screen Layout ---
# Which half of the screen to monitor for changes
MONITOR_SIDE = "left"  # "left" or "right"

# Where the prompt lives on the paste side
# "bottom_right" = bottom-right quadrant (right half, lower portion)
# "right"        = full right half
# "bottom_left"  = bottom-left quadrant
PASTE_ZONE = "bottom_right"

# --- Paste Zone Fine-Tuning ---
# For "bottom_right": how far down the SCREEN the prompt area starts (0.0-1.0)
# 0.52 = Gemini browser starts about halfway down the right side
PASTE_ZONE_TOP_RATIO = 0.52

# --- Change Detection ---
# How often to check for screen changes (seconds)
POLL_INTERVAL = 0.5

# Pixel difference threshold to count as a "change" (0-255)
PIXEL_THRESHOLD = 30

# Percentage of pixels that must differ to trigger capture (0.0-1.0)
CHANGE_PERCENT = 0.02  # 2% of pixels must change

# Cooldown after a paste before monitoring resumes (seconds)
COOLDOWN = 5.0

# --- Startup ---
# Countdown timer (seconds) before monitoring begins after toggle-on
STARTUP_DELAY = 5

# --- Automation ---
# Delay before clicking the paste target (seconds)
CLICK_DELAY = 0.3

# Delay after pasting before hitting submit (seconds)
ENTER_DELAY = 2.0

# Where to click for the INPUT BOX within the paste zone (relative)
# Paste zone is (960, 561) to (1920, 1080) on a 1920x1080 screen
# Gemini's "Ask Gemini" text input is about 75% down in that zone
PASTE_CLICK_X_RATIO = 0.5
PASTE_CLICK_Y_RATIO = 0.75

# Paste method: "clipboard" = Ctrl+V, "file_upload" = attach button + file dialog
PASTE_METHOD = "file_upload"

# Browser window title keywords — used to find and focus the correct window
# IMPORTANT: Don't include "Claude" if Claude Code is open (it would match this app!)
BROWSER_TITLE_KEYWORDS = ["Gemini", "ChatGPT"]

# Submit method: "enter" = press Enter key, "click_button" = click send button
SUBMIT_METHOD = "click_button"

# Where the Send/Submit button is within the paste zone (relative)
# Gemini's blue arrow ">" send button is at the far bottom-right
SUBMIT_BUTTON_X_RATIO = 0.97
SUBMIT_BUTTON_Y_RATIO = 0.96

# Where the attach/upload "+" button is within the paste zone
ATTACH_BUTTON_X_RATIO = 0.03
ATTACH_BUTTON_Y_RATIO = 0.96

# --- Hotkeys ---
TOGGLE_HOTKEY = "ctrl+shift+f9"
QUIT_HOTKEY = "ctrl+shift+f10"

# --- Logging ---
LOG_FILE = "split_screen.log"
LOG_LEVEL = "INFO"
