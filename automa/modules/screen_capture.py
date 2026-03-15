from __future__ import annotations

import mss
import numpy as np


class ScreenCapture:
    def __init__(self) -> None:
        self.sct = mss.mss()

    def capture(self, monitor_index: int = 1) -> np.ndarray:
        monitors = self.sct.monitors
        if len(monitors) <= 1:
            raise RuntimeError("No monitor available for capture")

        if monitor_index < 1 or monitor_index >= len(monitors):
            monitor_index = 1

        monitor = monitors[monitor_index]
        screenshot = self.sct.grab(monitor)
        frame = np.array(screenshot)
        if frame.ndim != 3 or frame.shape[2] < 3:
            raise RuntimeError("Unexpected frame shape from screen capture")
        return frame[:, :, :3]
