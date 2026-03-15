from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from automa.core.models import MacroGroup


class MacroStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.groups: list[MacroGroup] = []
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.groups = [MacroGroup(name="Default", macros=[])]
            self.save()
            return

        try:
            raw = self.path.read_text(encoding="utf-8")
            data: dict[str, Any] = json.loads(raw)
        except Exception:
            self.groups = [MacroGroup(name="Default", macros=[])]
            self.save()
            return

        groups_data = data.get("groups", []) if isinstance(data, dict) else []
        parsed_groups: list[MacroGroup] = []
        for item in groups_data:
            if not isinstance(item, dict):
                continue
            try:
                parsed_groups.append(MacroGroup.from_dict(item))
            except Exception:
                continue

        self.groups = parsed_groups or [MacroGroup(name="Default", macros=[])]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"groups": [group.to_dict() for group in self.groups]}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def import_file(self, file_path: Path) -> None:
        raw = file_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Imported macro file must contain a JSON object")

        groups_data = data.get("groups")
        if not isinstance(groups_data, list):
            raise ValueError("Imported macro file must contain a 'groups' array")

        parsed_groups: list[MacroGroup] = []
        for item in groups_data:
            if not isinstance(item, dict):
                continue
            parsed_groups.append(MacroGroup.from_dict(item))

        self.groups = parsed_groups or [MacroGroup(name="Default", macros=[])]
        self.save()

    def export_file(self, file_path: Path) -> None:
        payload = {"groups": [group.to_dict() for group in self.groups]}
        file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
