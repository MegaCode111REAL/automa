from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from automa.modules.screen_capture import ScreenCapture


@dataclass
class MatchResult:
    score: float
    top_left: tuple[int, int]
    center: tuple[int, int]


class ImageDetector:
    def __init__(self, capture: ScreenCapture | None = None) -> None:
        self.capture = capture or ScreenCapture()

    def find_matches(self, template_path: Path, threshold: float = 0.8, max_results: int = 5) -> list[MatchResult]:
        screen = self.capture.capture()
        template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
        if template is None:
            raise FileNotFoundError(f"Template not found: {template_path}")

        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)
        h, w = template.shape[:2]

        matches: list[MatchResult] = []
        for y, x in zip(*locations):
            score = float(result[y, x])
            center = (int(x + w / 2), int(y + h / 2))
            matches.append(MatchResult(score=score, top_left=(int(x), int(y)), center=center))

        matches.sort(key=lambda item: item.score, reverse=True)
        return matches[:max_results]

    def find_best_match(self, template_path: Path, threshold: float = 0.8) -> MatchResult | None:
        matches = self.find_matches(template_path=template_path, threshold=threshold, max_results=1)
        return matches[0] if matches else None
