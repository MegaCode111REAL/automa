from __future__ import annotations

import mss
import numpy as np


class ScreenCapture:
    def __init__(self) -> None:
        self.sct = mss.mss()

    def capture(self, monitor_index: int = 1) -> np.ndarray:
        monitor = self.sct.monitors[monitor_index]
        screenshot = self.sct.grab(monitor)
        frame = np.array(screenshot)
        return frame[:, :, :3]
