from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class GroupManager(QWidget):
    group_selected = Signal(int)
    create_group = Signal(str)
    delete_group = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.group_selected.emit)

        add_btn = QPushButton("+")
        del_btn = QPushButton("-")
        add_btn.clicked.connect(self._prompt_add)
        del_btn.clicked.connect(lambda: self.delete_group.emit(self.list_widget.currentRow()))

        button_row = QHBoxLayout()
        button_row.addWidget(add_btn)
        button_row.addWidget(del_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
        layout.addLayout(button_row)

    def set_groups(self, names: list[str]) -> None:
        self.list_widget.clear()
        self.list_widget.addItems(names)
        if names:
            self.list_widget.setCurrentRow(0)

    def _prompt_add(self) -> None:
        name, ok = QInputDialog.getText(self, "Create Group", "Group name:")
        if ok and name.strip():
            self.create_group.emit(name.strip())
