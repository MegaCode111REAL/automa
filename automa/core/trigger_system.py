from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable

from pynput import keyboard

from automa.core.models import Macro
from automa.modules.image_detection import ImageDetector

try:
    import pywinctl
except Exception:  # pragma: no cover - optional dependency on some environments
    pywinctl = None


class TriggerSystem:
    def __init__(self) -> None:
        self.image_detector = ImageDetector()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._hotkey_listener: keyboard.GlobalHotKeys | None = None

    def start(self, macros: list[Macro], on_trigger: Callable[[Macro], None], on_log: Callable[[str], None] | None = None) -> None:
        self.stop()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker, args=(macros, on_trigger, on_log), daemon=True)
        self._thread.start()

        hotkey_map = {}
        for macro in macros:
            if macro.trigger and macro.trigger.type == "hotkey":
                hotkey = macro.trigger.config.get("combo")
                if hotkey:
                    hotkey_map[hotkey] = lambda m=macro: on_trigger(m)
        if hotkey_map:
            self._hotkey_listener = keyboard.GlobalHotKeys(hotkey_map)
            self._hotkey_listener.start()

    def _worker(self, macros: list[Macro], on_trigger: Callable[[Macro], None], on_log: Callable[[str], None] | None) -> None:
        while not self._stop_event.is_set():
            for macro in macros:
                trigger = macro.trigger
                if not trigger:
                    continue
                if trigger.type == "window_active":
                    if pywinctl is None:
                        continue
                    target = str(trigger.config.get("window_name", ""))
                    active = pywinctl.getActiveWindowTitle() or ""
                    if target and target.lower() in active.lower():
                        on_trigger(macro)
                        if on_log:
                            on_log(f"Window trigger matched: {macro.name}")
                elif trigger.type == "timer":
                    interval = float(trigger.config.get("interval", 10))
                    last_run = float(trigger.config.get("_last_run", 0))
                    now = time.time()
                    if now - last_run >= interval:
                        trigger.config["_last_run"] = now
                        on_trigger(macro)
                elif trigger.type == "image_detect":
                    template = trigger.config.get("template")
                    threshold = float(trigger.config.get("threshold", 0.9))
                    if template:
                        match = self.image_detector.find_best_match(Path(template), threshold=threshold)
                        if match:
                            on_trigger(macro)
                            if on_log:
                                on_log(f"Image trigger matched: {macro.name} ({match.score:.2f})")
            time.sleep(0.5)

    def stop(self) -> None:
        self._stop_event.set()
        if self._hotkey_listener:
            self._hotkey_listener.stop()
            self._hotkey_listener = None
