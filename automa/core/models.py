from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Action:
    type: str
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = {"type": self.type}
        payload.update(self.params)
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Action":
        payload = dict(data)
        action_type = str(payload.pop("type", "delay"))
        return cls(type=action_type, params=payload)


@dataclass
class Macro:
    name: str
    author: str = "Unknown"
    keybind: str = ""
    actions: list[Action] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "author": self.author,
            "keybind": self.keybind,
            "events": [action.to_dict() for action in self.actions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Macro":
        event_items = data.get("events", data.get("actions", []))
        actions = [Action.from_dict(item) for item in event_items if isinstance(item, dict)]
        return cls(
            name=str(data.get("name", "Untitled Macro")),
            author=str(data.get("author", "Unknown")),
            keybind=str(data.get("keybind", "")),
            actions=actions,
        )


@dataclass
class Setup:
    name: str
    author: str = "Unknown"
    macros: list[Macro] = field(default_factory=list)
    active: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "author": self.author,
            "active": self.active,
            "macros": [macro.to_dict() for macro in self.macros],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Setup":
        macros = [Macro.from_dict(item) for item in data.get("macros", []) if isinstance(item, dict)]
        return cls(
            name=str(data.get("name", "Untitled Setup")),
            author=str(data.get("author", "Unknown")),
            macros=macros,
            active=bool(data.get("active", False)),
        )
