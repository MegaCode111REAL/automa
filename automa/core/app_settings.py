from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class AppSettings:
    """Persist small UI/app flags in a per-user config file."""

    def __init__(self) -> None:
        self.path = self._default_path()
        self._data: dict[str, Any] = {}
        self.load()

    def _default_path(self) -> Path:
        if os.name == "nt":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        elif os.name == "posix" and "darwin" in os.uname().sysname.lower():
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path.home() / ".config"
        return base / "automa" / "settings.json"

    def load(self) -> None:
        if not self.path.exists():
            self._data = {}
            return
        try:
            self._data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            self._data = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self._data.get(key, default)
        return bool(value)

    def set_bool(self, key: str, value: bool) -> None:
        self._data[key] = bool(value)
        self.save()
