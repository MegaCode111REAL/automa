from __future__ import annotations

import json
from pathlib import Path

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
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.groups = [MacroGroup.from_dict(item) for item in data.get("groups", [])]
        if not self.groups:
            self.groups = [MacroGroup(name="Default", macros=[])]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"groups": [group.to_dict() for group in self.groups]}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def import_file(self, file_path: Path) -> None:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        self.groups = [MacroGroup.from_dict(item) for item in data.get("groups", [])]
        self.save()

    def export_file(self, file_path: Path) -> None:
        payload = {"groups": [group.to_dict() for group in self.groups]}
        file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
