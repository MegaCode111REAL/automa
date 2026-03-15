from __future__ import annotations

from dataclasses import asdict, dataclass, field
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
        action_type = payload.pop("type")
        return cls(type=action_type, params=payload)


@dataclass
class Trigger:
    type: str
    config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, **self.config}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Trigger":
        payload = dict(data)
        trigger_type = payload.pop("type")
        return cls(type=trigger_type, config=payload)


@dataclass
class Macro:
    name: str
    actions: list[Action] = field(default_factory=list)
    trigger: Trigger | None = None

    def to_dict(self) -> dict[str, Any]:
        serialized = {
            "name": self.name,
            "actions": [action.to_dict() for action in self.actions],
        }
        if self.trigger:
            serialized["trigger"] = self.trigger.to_dict()
        return serialized

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Macro":
        actions = [Action.from_dict(item) for item in data.get("actions", [])]
        trigger_data = data.get("trigger")
        trigger = Trigger.from_dict(trigger_data) if trigger_data else None
        return cls(name=data["name"], actions=actions, trigger=trigger)


@dataclass
class MacroGroup:
    name: str
    macros: list[Macro] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "macros": [macro.to_dict() for macro in self.macros]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MacroGroup":
        return cls(name=data["name"], macros=[Macro.from_dict(item) for item in data.get("macros", [])])
