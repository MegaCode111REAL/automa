from __future__ import annotations

import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from automa.core.models import Action, Macro


class MacroEditor(QWidget):
    macro_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.current_macro: Macro | None = None
        self.actions_list = QListWidget()
        self.actions_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.actions_list.setDragDropMode(QAbstractItemView.InternalMove)

        self.json_editor = QTextEdit()
        self.json_editor.setPlaceholderText('{"type": "delay", "time": 0.25}')

        add_btn = QPushButton("Add Action JSON")
        delete_btn = QPushButton("Delete Selected")
        save_btn = QPushButton("Apply Edit")

        add_btn.clicked.connect(self._add_action)
        delete_btn.clicked.connect(self._delete_action)
        save_btn.clicked.connect(self._save_selected)
        self.actions_list.currentRowChanged.connect(self._fill_action_editor)

        button_row = QHBoxLayout()
        button_row.addWidget(add_btn)
        button_row.addWidget(delete_btn)
        button_row.addWidget(save_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Macro Actions"))
        layout.addWidget(self.actions_list)
        layout.addWidget(QLabel("Action JSON"))
        layout.addWidget(self.json_editor)
        layout.addLayout(button_row)

    def set_macro(self, macro: Macro | None) -> None:
        self.current_macro = macro
        self.actions_list.clear()
        if not macro:
            self.json_editor.clear()
            return
        for action in macro.actions:
            self.actions_list.addItem(self._format_action(action))

    def commit_reorder(self) -> None:
        if not self.current_macro:
            return
        updated: list[Action] = []
        for i in range(self.actions_list.count()):
            item = self.actions_list.item(i)
            action_data = item.data(Qt.UserRole)
            if action_data:
                updated.append(Action.from_dict(action_data))
        self.current_macro.actions = updated
        self.macro_changed.emit()

    def _format_action(self, action: Action) -> QListWidgetItem:
        text = f"{action.type} {action.params}"
        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, action.to_dict())
        return item

    def _add_action(self) -> None:
        if not self.current_macro:
            return
        try:
            data = json.loads(self.json_editor.toPlainText())
            action = Action.from_dict(data)
        except Exception:
            return
        self.current_macro.actions.append(action)
        self.actions_list.addItem(self._format_action(action))
        self.macro_changed.emit()

    def _delete_action(self) -> None:
        if not self.current_macro:
            return
        row = self.actions_list.currentRow()
        if row < 0:
            return
        self.actions_list.takeItem(row)
        self.current_macro.actions.pop(row)
        self.macro_changed.emit()

    def _fill_action_editor(self, row: int) -> None:
        if row < 0:
            return
        item = self.actions_list.item(row)
        data = item.data(Qt.UserRole)
        self.json_editor.setPlainText(json.dumps(data, indent=2))

    def _save_selected(self) -> None:
        if not self.current_macro:
            return
        row = self.actions_list.currentRow()
        if row < 0:
            return
        try:
            data = json.loads(self.json_editor.toPlainText())
            action = Action.from_dict(data)
        except Exception:
            return
        self.current_macro.actions[row] = action
        self.actions_list.item(row).setText(f"{action.type} {action.params}")
        self.actions_list.item(row).setData(Qt.UserRole, action.to_dict())
        self.macro_changed.emit()
