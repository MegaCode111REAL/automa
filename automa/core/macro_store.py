from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from automa.core.models import Macro, Setup


class MacroStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.setups: list[Setup] = []
        self.load()

    @property
    def groups(self) -> list[Setup]:
        """Backward-compatible alias for older UI code."""
        return self.setups

    def load(self) -> None:
        if not self.path.exists():
            self.setups = [Setup(name="Default Setup", author="Unknown", macros=[], active=True)]
            self.save()
            return

        try:
            raw = self.path.read_text(encoding="utf-8")
            data: dict[str, Any] = json.loads(raw)
        except Exception:
            self.setups = [Setup(name="Default Setup", author="Unknown", macros=[], active=True)]
            self.save()
            return

        parsed: list[Setup] = []
        if isinstance(data, dict) and isinstance(data.get("setups"), list):
            for item in data["setups"]:
                if isinstance(item, dict):
                    parsed.append(Setup.from_dict(item))
        elif isinstance(data, dict) and isinstance(data.get("groups"), list):
            # Legacy format migration.
            for item in data["groups"]:
                if not isinstance(item, dict):
                    continue
                macros = [Macro.from_dict(m) for m in item.get("macros", []) if isinstance(m, dict)]
                parsed.append(Setup(name=str(item.get("name", "Imported Setup")), author="Unknown", macros=macros, active=False))

        self.setups = parsed or [Setup(name="Default Setup", author="Unknown", macros=[], active=True)]
        self.ensure_single_active()

    def ensure_single_active(self) -> None:
        first = None
        for idx, setup in enumerate(self.setups):
            if setup.active and first is None:
                first = idx
            elif setup.active:
                setup.active = False
        if first is None and self.setups:
            self.setups[0].active = True

    def save(self) -> None:
        self.ensure_single_active()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"setups": [setup.to_dict() for setup in self.setups]}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def export_setup(self, setup: Setup, file_path: Path) -> None:
        payload = setup.to_dict()
        file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def import_setup(self, file_path: Path) -> Setup:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Setup file must be a JSON object")
        setup = Setup.from_dict(data)
        self.setups.append(setup)
        self.ensure_single_active()
        self.save()
        return setup

    def export_macro(self, macro: Macro, file_path: Path) -> None:
        payload = macro.to_dict()
        file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def import_macro(self, file_path: Path) -> Macro:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Macro file must be a JSON object")
        return Macro.from_dict(data)
