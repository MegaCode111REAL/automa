from __future__ import annotations

import pyautogui


class KeyboardController:
    def press(self, key: str) -> None:
        pyautogui.keyDown(key)

    def release(self, key: str) -> None:
        pyautogui.keyUp(key)

    def tap(self, key: str) -> None:
        pyautogui.press(key)

    def type_text(self, text: str) -> None:
        pyautogui.write(text)
