"""Overlay window — always-on-top status display with countdown timer."""

import logging
import tkinter as tk
import threading
import queue

logger = logging.getLogger(__name__)


class StatusOverlay:
    """A small always-on-top window showing app status and countdown."""

    def __init__(self):
        self._root = None
        self._label = None
        self._ready = threading.Event()
        self._update_queue = queue.Queue()
        self._thread = threading.Thread(target=self._run_tk, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=5)

    def _run_tk(self):
        self._root = tk.Tk()
        self._root.title("SSPP")
        self._root.attributes("-topmost", True)
        self._root.overrideredirect(True)  # no title bar

        # Position: top-center of screen
        screen_w = self._root.winfo_screenwidth()
        win_w, win_h = 340, 54
        x = (screen_w - win_w) // 2
        y = 8
        self._root.geometry(f"{win_w}x{win_h}+{x}+{y}")

        self._root.configure(bg="#1a1a2e")

        self._label = tk.Label(
            self._root,
            text="SSPP: PAUSED",
            font=("Consolas", 16, "bold"),
            fg="#888888",
            bg="#1a1a2e",
            padx=12,
            pady=6,
        )
        self._label.pack(fill="both", expand=True)

        self._ready.set()
        self._root.after(50, self._process_updates)
        self._root.mainloop()

    def update(self, text, color="#00cc55"):
        """Update the overlay text and color. Thread-safe via queue."""
        try:
            self._update_queue.put((text, color))
        except Exception:
            logger.debug("Overlay update failed (queue may be closed)")

    def _process_updates(self):
        try:
            while not self._update_queue.empty():
                text, color = self._update_queue.get_nowait()
                self._label.config(text=text, fg=color)
        except Exception:
            logger.debug("Overlay update processing failed")
        if self._root:
            self._root.after(50, self._process_updates)

    def destroy(self):
        if self._root:
            try:
                self._root.after(0, self._root.destroy)
            except Exception:
                logger.debug("Overlay destroy failed (already closed)")
