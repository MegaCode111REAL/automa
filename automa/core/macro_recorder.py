from __future__ import annotations

import threading
import time
from typing import Callable

from pynput import keyboard, mouse

from automa.core.models import Action, Macro


class MacroRecorder:
    def __init__(self) -> None:
        self._actions: list[Action] = []
        self._start_time = 0.0
        self._last_event_time = 0.0
        self._recording = False
        self._keyboard_listener: keyboard.Listener | None = None
        self._mouse_listener: mouse.Listener | None = None
        self._lock = threading.Lock()

    def start(self, on_log: Callable[[str], None] | None = None) -> bool:
        if self._recording:
            if on_log:
                on_log("Recording is already running")
            return False

        self._actions = []
        self._start_time = time.time()
        self._last_event_time = self._start_time
        self._recording = True

        def keyboard_press(key: keyboard.Key | keyboard.KeyCode) -> None:
            with self._lock:
                if not self._recording:
                    return
                key_name = self._safe_key_name(key)
                self._push_delay()
                self._actions.append(Action(type="keyboard_down", params={"key": key_name}))

        def keyboard_release(key: keyboard.Key | keyboard.KeyCode) -> None:
            with self._lock:
                if not self._recording:
                    return
                key_name = self._safe_key_name(key)
                self._push_delay()
                self._actions.append(Action(type="keyboard_up", params={"key": key_name}))

        def mouse_move(x: int, y: int) -> None:
            with self._lock:
                if not self._recording:
                    return
                self._push_delay()
                self._actions.append(Action(type="mouse_move", params={"x": x, "y": y}))

        def mouse_click(x: int, y: int, button: mouse.Button, pressed: bool) -> None:
            with self._lock:
                if not self._recording or not pressed:
                    return
                self._push_delay()
                self._actions.append(Action(type="mouse_click", params={"x": x, "y": y, "button": button.name}))

        def mouse_scroll(x: int, y: int, dx: int, dy: int) -> None:
            with self._lock:
                if not self._recording:
                    return
                self._push_delay()
                self._actions.append(Action(type="mouse_scroll", params={"amount": dy * 120}))

        try:
            self._keyboard_listener = keyboard.Listener(on_press=keyboard_press, on_release=keyboard_release)
            self._mouse_listener = mouse.Listener(on_move=mouse_move, on_click=mouse_click, on_scroll=mouse_scroll)
            self._keyboard_listener.start()
            self._mouse_listener.start()
        except Exception as exc:
            self._recording = False
            if on_log:
                on_log(f"Failed to start recorder: {exc}")
            return False

        if on_log:
            on_log("Recording started")
        return True

    def stop(self, macro_name: str = "recorded_macro", on_log: Callable[[str], None] | None = None) -> Macro:
        with self._lock:
            self._recording = False

        if self._keyboard_listener:
            try:
                self._keyboard_listener.stop()
            except Exception:
                pass
            self._keyboard_listener = None

        if self._mouse_listener:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass
            self._mouse_listener = None

        safe_name = macro_name.strip() or "recorded_macro"
        macro = Macro(name=safe_name, actions=list(self._actions))
        if on_log:
            on_log(f"Recording stopped. Captured {len(self._actions)} actions")
        return macro

    def _push_delay(self) -> None:
        now = time.time()
        delay = now - self._last_event_time
        self._last_event_time = now
        if delay > 0.01:
            self._actions.append(Action(type="delay", params={"time": round(delay, 3)}))

    @staticmethod
    def _safe_key_name(key: keyboard.Key | keyboard.KeyCode) -> str:
        if hasattr(key, "char") and getattr(key, "char"):
            return str(getattr(key, "char"))
        return str(key).replace("Key.", "")
