from __future__ import annotations

import pyautogui


class MouseController:
    def move(self, x: int, y: int, duration: float = 0.0) -> None:
        pyautogui.moveTo(x, y, duration=duration)

    def click(self, button: str = "left", x: int | None = None, y: int | None = None) -> None:
        pyautogui.click(x=x, y=y, button=button)

    def scroll(self, amount: int) -> None:
        pyautogui.scroll(amount)

    def position(self) -> tuple[int, int]:
        point = pyautogui.position()
        return point.x, point.y
