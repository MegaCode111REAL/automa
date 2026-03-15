from __future__ import annotations

import threading
import time
from typing import Callable

import pyautogui

from automa.core.models import Macro
from automa.modules.keyboard_controller import KeyboardController
from automa.modules.mouse_controller import MouseController


class MacroEngine:
    def __init__(self) -> None:
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.thread: threading.Thread | None = None
        pyautogui.FAILSAFE = True

    def play(self, macro: Macro, speed: float = 1.0, loop: bool = False, on_log: Callable[[str], None] | None = None) -> bool:
        if self.thread and self.thread.is_alive():
            if on_log:
                on_log("Playback already running")
            return False

        if not macro.actions:
            if on_log:
                on_log(f"Macro '{macro.name}' has no actions")
            return False

        safe_speed = max(float(speed), 0.01)
        self.stop_event.clear()
        self.pause_event.clear()
        self.thread = threading.Thread(
            target=self._play_worker,
            args=(macro, safe_speed, loop, on_log),
            daemon=True,
        )
        self.thread.start()
        return True

    def _play_worker(self, macro: Macro, speed: float, loop: bool, on_log: Callable[[str], None] | None) -> None:
        try:
            while not self.stop_event.is_set():
                for idx, action in enumerate(macro.actions):
                    if self.stop_event.is_set():
                        break
                    while self.pause_event.is_set() and not self.stop_event.is_set():
                        time.sleep(0.05)
                    try:
                        self._run_action(action.type, action.params, speed)
                    except pyautogui.FailSafeException:
                        self.stop_event.set()
                        if on_log:
                            on_log("Failsafe triggered: playback stopped")
                        break
                    except Exception as exc:
                        if on_log:
                            on_log(f"Action {idx} ({action.type}) failed: {exc}")
                if not loop:
                    break
        finally:
            if on_log:
                on_log(f"Playback finished for macro: {macro.name}")

    def _run_action(self, action_type: str, params: dict, speed: float) -> None:
        if action_type == "delay":
            delay = max(0.0, float(params.get("time", 0.1)))
            time.sleep(delay / speed)
        elif action_type == "mouse_move":
            self.mouse.move(int(params.get("x", 0)), int(params.get("y", 0)), duration=0)
        elif action_type == "mouse_click":
            x = params.get("x")
            y = params.get("y")
            self.mouse.click(
                button=str(params.get("button", "left")),
                x=int(x) if x is not None else None,
                y=int(y) if y is not None else None,
            )
        elif action_type == "mouse_scroll":
            self.mouse.scroll(int(params.get("amount", 0)))
        elif action_type == "key_press":
            self.keyboard.tap(str(params.get("key", "")))
        elif action_type == "keyboard_down":
            self.keyboard.press(str(params.get("key", "")))
        elif action_type == "keyboard_up":
            self.keyboard.release(str(params.get("key", "")))
        elif action_type == "text":
            self.keyboard.type_text(str(params.get("value", "")))

    def stop(self) -> None:
        self.stop_event.set()

    def pause(self) -> None:
        self.pause_event.set()

    def resume(self) -> None:
        self.pause_event.clear()
