# Copyright (c) 2026 Nardo. AGPL-3.0 — see LICENSE
#!/usr/bin/env python3
"""
Always-running menubar/tray indicator.
Shows recording state via system tray icon.
Start once: nohup python3 ~/recording_indicator.py &
"""
import os
import sys
import threading
import time

# Try rumps (macOS), then pystray (Linux), else stub
_backend = None
try:
    import rumps
    _backend = "rumps"
except ImportError:
    try:
        import pystray
        from PIL import Image, ImageDraw
        _backend = "pystray"
    except ImportError:
        _backend = None

# Single-instance lock
LOCK_FILE = "/tmp/recording_indicator.pid"
if os.path.exists(LOCK_FILE):
    try:
        old_pid = int(open(LOCK_FILE).read())
        os.kill(old_pid, 0)  # check if alive
        print(f"Already running (PID {old_pid}), exiting.")
        sys.exit(0)
    except (ProcessLookupError, ValueError):
        pass  # stale lock, continue
open(LOCK_FILE, "w").write(str(os.getpid()))

RECORDING_FILE = "/tmp/recording_active"
TRANSCRIBING_FILE = "/tmp/transcribing_active"
ERROR_FILE = "/tmp/transcribe_error"
MUTE_FILE = "/tmp/tts_muted"
VAD_MODE_FILE = "/tmp/vad_mode"
WAKE_WORD_FILE = "/tmp/wake_word_mode"

# ── State resolution (shared across backends) ────────────────────────────────

def _resolve_state():
    """Return (mute_prefix, state_icon) tuple."""
    mute = "\U0001f507" if os.path.exists(MUTE_FILE) else ""  # 🔇

    if os.path.exists(RECORDING_FILE):
        state = "\U0001f534"  # 🔴
    elif os.path.exists(TRANSCRIBING_FILE):
        state = "\U0001f7e1"  # 🟡
    elif os.path.exists(ERROR_FILE):
        state = "\u26a0\ufe0f"  # ⚠️
    elif os.path.exists(WAKE_WORD_FILE):
        state = "\U0001f442"  # 👂
    elif os.path.exists(VAD_MODE_FILE):
        state = "\U0001f7e2"  # 🟢
    else:
        state = "\u2325"  # ⌥

    return mute + state


if _backend == "rumps":

    class RecordingIndicator(rumps.App):
        def __init__(self):
            super().__init__("", quit_button=None)
            self.title = ""
            threading.Thread(target=self._watch, daemon=True).start()

        def _watch(self):
            last = None
            flash = False
            ticks = 0
            while True:
                mute = "\U0001f507" if os.path.exists(MUTE_FILE) else ""

                if os.path.exists(RECORDING_FILE):
                    state = "\U0001f534"
                elif os.path.exists(TRANSCRIBING_FILE):
                    state = "\U0001f7e1"
                elif os.path.exists(ERROR_FILE):
                    ticks += 1
                    if ticks >= 3:
                        flash = not flash
                        ticks = 0
                    state = "\u26a0\ufe0f" if flash else "\U0001f7e1"
                elif os.path.exists(WAKE_WORD_FILE):
                    state = "\U0001f442"  # 👂
                elif os.path.exists(VAD_MODE_FILE):
                    state = "\U0001f7e2"
                else:
                    state = "\u2325"

                state = mute + state
                if state != last:
                    self.title = state
                    last = state
                time.sleep(0.1)

elif _backend == "pystray":

    _STATE_COLORS = {
        "\U0001f534": "red",
        "\U0001f7e1": "yellow",
        "\u26a0\ufe0f": "orange",
        "\U0001f442": "purple",
        "\U0001f7e2": "green",
        "\u2325": "gray",
    }

    def _make_icon_image(color="gray", size=64):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, size - 4, size - 4], fill=color)
        return img

    class RecordingIndicator:
        def __init__(self):
            self._icon = pystray.Icon(
                "voice_indicator",
                _make_icon_image("gray"),
                "Voice Daemon",
            )
            threading.Thread(target=self._watch, daemon=True).start()

        def _watch(self):
            last = None
            while True:
                state = _resolve_state()
                if state != last:
                    # Extract the state part (skip mute prefix)
                    core = state.replace("\U0001f507", "")
                    color = _STATE_COLORS.get(core, "gray")
                    self._icon.icon = _make_icon_image(color)
                    self._icon.title = state
                    last = state
                time.sleep(0.1)

        def run(self):
            self._icon.run()

else:

    class RecordingIndicator:
        """Stub — no tray backend available."""
        def __init__(self):
            print("No tray indicator backend available (install rumps or pystray).", flush=True)

        def run(self):
            # Block forever so the process doesn't exit
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                pass


if __name__ == "__main__":
    if _backend == "rumps":
        # Hide from Dock (menubar-only app)
        import AppKit
        info = AppKit.NSBundle.mainBundle().infoDictionary()
        info["LSUIElement"] = "1"
    RecordingIndicator().run()
