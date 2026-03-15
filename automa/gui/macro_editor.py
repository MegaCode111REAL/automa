from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from automa.core.macro_recorder import MacroRecorder
from automa.core.models import Action, Macro
from automa.core.macro_store import MacroStore


class MacroEditorWindow(QMainWindow):
    macro_saved = Signal()

    def __init__(self, macro: Macro, store: MacroStore) -> None:
        super().__init__()
        self.macro = macro
        self.store = store
        self.recorder = MacroRecorder()
        self.recording = False

        self.setWindowTitle(f"Macro Editor - {macro.name}")
        self.resize(900, 540)

        self.name_label = QLabel(macro.name)

        self.events_list = QListWidget()
        self.events_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.events_list.currentRowChanged.connect(self._event_selected)
        self.events_list.model().rowsMoved.connect(lambda *_: self._sync_order_from_list())

        self.add_btn = QPushButton("Add")
        self.del_btn = QPushButton("Delete")
        self.rec_btn = QPushButton("Record")
        self.save_btn = QPushButton("Save")
        self.export_btn = QPushButton("Export")

        self.add_type = QComboBox()
        self.add_type.addItems(["Keyboard", "Delay", "Mouse"])

        self.add_btn.clicked.connect(self._add_event)
        self.del_btn.clicked.connect(self._delete_event)
        self.rec_btn.clicked.connect(self._toggle_record)
        self.save_btn.clicked.connect(self._save)
        self.export_btn.clicked.connect(self._export)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(self.name_label)

        row = QHBoxLayout()
        row.addWidget(self.add_btn)
        row.addWidget(self.add_type)
        row.addWidget(self.del_btn)
        row.addWidget(self.rec_btn)
        row.addWidget(self.save_btn)
        row.addWidget(self.export_btn)
        left_layout.addLayout(row)
        left_layout.addWidget(self.events_list)

        self.type_dropdown = QComboBox()
        self.type_dropdown.addItems(["keyboard", "delay", "mouse"])
        self.type_dropdown.currentTextChanged.connect(self._apply_properties)

        self.key_field = QLineEdit()
        self.key_action = QComboBox()
        self.key_action.addItems(["down", "up"])

        self.mouse_button = QComboBox()
        self.mouse_button.addItems(["left", "right", "middle"])
        self.mouse_action = QComboBox()
        self.mouse_action.addItems(["down", "up", "move"])
        self.mouse_x = QSpinBox()
        self.mouse_x.setMaximum(99999)
        self.mouse_y = QSpinBox()
        self.mouse_y.setMaximum(99999)

        self.delay_ms = QSpinBox()
        self.delay_ms.setMaximum(300000)
        self.delay_ms.setSuffix(" ms")

        for w in [self.key_field, self.key_action, self.mouse_button, self.mouse_action, self.mouse_x, self.mouse_y, self.delay_ms]:
            if hasattr(w, "valueChanged"):
                w.valueChanged.connect(self._apply_properties)
            if hasattr(w, "textChanged"):
                w.textChanged.connect(self._apply_properties)
            if hasattr(w, "currentTextChanged"):
                w.currentTextChanged.connect(self._apply_properties)

        props_widget = QWidget()
        props_layout = QFormLayout(props_widget)
        props_layout.addRow("Type", self.type_dropdown)
        props_layout.addRow("Keyboard key", self.key_field)
        props_layout.addRow("Keyboard action", self.key_action)
        props_layout.addRow("Mouse button", self.mouse_button)
        props_layout.addRow("Mouse action", self.mouse_action)
        props_layout.addRow("Mouse X", self.mouse_x)
        props_layout.addRow("Mouse Y", self.mouse_y)
        props_layout.addRow("Delay", self.delay_ms)

        split = QSplitter()
        split.addWidget(left)
        split.addWidget(props_widget)
        split.setSizes([620, 280])

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.addWidget(split)
        self.setCentralWidget(root)

        self._refresh_events()

    def _refresh_events(self) -> None:
        self.events_list.clear()
        for idx, action in enumerate(self.macro.actions, start=1):
            text = self._action_text(action, idx)
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, action.to_dict())
            self.events_list.addItem(item)

    def _action_text(self, action: Action, index: int) -> str:
        if action.type == "mouse":
            return f"{index}. {action.params.get('button', 'left').title()} mouse ({action.params.get('action', 'down')})"
        if action.type == "keyboard":
            return f"{index}. Keyboard {action.params.get('key', '').upper()} ({action.params.get('action', 'down')})"
        if action.type == "delay":
            return f"{index}. Delay ({action.params.get('ms', 0)}ms)"
        return f"{index}. {action.type}"

    def _add_event(self) -> None:
        kind = self.add_type.currentText().lower()
        if kind == "keyboard":
            action = Action(type="keyboard", params={"key": "a", "action": "down"})
        elif kind == "mouse":
            action = Action(type="mouse", params={"button": "left", "action": "down", "x": 0, "y": 0})
        else:
            action = Action(type="delay", params={"ms": 250})
        self.macro.actions.append(action)
        self._refresh_events()
        self.events_list.setCurrentRow(self.events_list.count() - 1)

    def _delete_event(self) -> None:
        row = self.events_list.currentRow()
        if row < 0:
            return
        self.macro.actions.pop(row)
        self._refresh_events()

    def _toggle_record(self) -> None:
        if not self.recording:
            started = self.recorder.start(on_log=None)
            if started:
                self.recording = True
                self.rec_btn.setText("Stop")
            else:
                QMessageBox.warning(self, "Record", "Failed to start recorder.")
            return

        recorded = self.recorder.stop(macro_name=self.macro.name, on_log=None)
        converted: list[Action] = []
        for action in recorded.actions:
            if action.type == "mouse_click":
                button = action.params.get("button", "left")
                x = int(action.params.get("x", 0))
                y = int(action.params.get("y", 0))
                converted.append(Action(type="mouse", params={"button": button, "action": "down", "x": x, "y": y}))
                converted.append(Action(type="mouse", params={"button": button, "action": "up", "x": x, "y": y}))
            elif action.type == "keyboard_down":
                converted.append(Action(type="keyboard", params={"key": str(action.params.get("key", "")), "action": "down"}))
            elif action.type == "keyboard_up":
                converted.append(Action(type="keyboard", params={"key": str(action.params.get("key", "")), "action": "up"}))
            elif action.type == "delay":
                converted.append(Action(type="delay", params={"ms": int(float(action.params.get("time", 0)) * 1000)}))
            elif action.type == "mouse_move":
                converted.append(Action(type="mouse", params={"button": "left", "action": "move", "x": int(action.params.get("x", 0)), "y": int(action.params.get("y", 0))}))
        self.macro.actions.extend(converted)

        self.recording = False
        self.rec_btn.setText("Record")
        self._refresh_events()

    def _event_selected(self, row: int) -> None:
        if row < 0 or row >= len(self.macro.actions):
            return
        action = self.macro.actions[row]
        self.type_dropdown.setCurrentText(action.type)
        self.key_field.setText(str(action.params.get("key", "")))
        self.key_action.setCurrentText(str(action.params.get("action", "down")))
        self.mouse_button.setCurrentText(str(action.params.get("button", "left")))
        self.mouse_action.setCurrentText(str(action.params.get("action", "down")))
        self.mouse_x.setValue(int(action.params.get("x", 0)))
        self.mouse_y.setValue(int(action.params.get("y", 0)))
        self.delay_ms.setValue(int(action.params.get("ms", 0)))

    def _apply_properties(self) -> None:
        row = self.events_list.currentRow()
        if row < 0 or row >= len(self.macro.actions):
            return
        t = self.type_dropdown.currentText()
        if t == "keyboard":
            action = Action(type="keyboard", params={"key": self.key_field.text(), "action": self.key_action.currentText()})
        elif t == "mouse":
            action = Action(
                type="mouse",
                params={
                    "button": self.mouse_button.currentText(),
                    "action": self.mouse_action.currentText(),
                    "x": self.mouse_x.value(),
                    "y": self.mouse_y.value(),
                },
            )
        else:
            action = Action(type="delay", params={"ms": self.delay_ms.value()})
        self.macro.actions[row] = action
        self._refresh_events()
        self.events_list.setCurrentRow(row)

    def _sync_order_from_list(self) -> None:
        updated: list[Action] = []
        for i in range(self.events_list.count()):
            data = self.events_list.item(i).data(Qt.UserRole)
            if isinstance(data, dict):
                updated.append(Action.from_dict(data))
        self.macro.actions = updated
        self._refresh_events()

    def _save(self) -> None:
        self.store.save()
        self.macro_saved.emit()
        QMessageBox.information(self, "Saved", "Macro saved.")

    def _export(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Macro", filter="automa Macro (*.atm)")
        if not file_path:
            return
        path = file_path if file_path.endswith(".atm") else f"{file_path}.atm"
        self.store.export_macro(self.macro, Path(path))
        QMessageBox.information(self, "Exported", f"Exported macro to {path}")
