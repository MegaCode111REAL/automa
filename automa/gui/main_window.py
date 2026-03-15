from __future__ import annotations

import getpass
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from automa.core.app_settings import AppSettings
from automa.core.macro_store import MacroStore
from automa.core.models import Macro, Setup
from automa.gui.macro_editor import MacroEditorWindow


class MainWindow(QMainWindow):
    def __init__(self, store: MacroStore) -> None:
        super().__init__()
        self.store = store
        self.settings = AppSettings()
        self.current_setup_index = -1
        self._open_editors: list[MacroEditorWindow] = []

        self.setWindowTitle("automa")
        self.resize(1024, 720)
        self.setAcceptDrops(True)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.setup_list_view = self._build_setup_list_view()
        self.setup_editor_view = self._build_setup_editor_view()

        self.stack.addWidget(self.setup_list_view)
        self.stack.addWidget(self.setup_editor_view)
        self._refresh_setups()
        self.show_setups_view()

    def _build_header_buttons(self, include_import: bool = True) -> tuple[QWidget, dict[str, QPushButton]]:
        row_widget = QWidget()
        row = QHBoxLayout(row_widget)
        row.setContentsMargins(0, 0, 0, 0)

        names = ["New", "Delete", "Rename"] + (["Import"] if include_import else []) + ["Export"]
        buttons: dict[str, QPushButton] = {}
        for name in names:
            btn = QPushButton(name)
            row.addWidget(btn)
            buttons[name.lower()] = btn
        row.addStretch(1)
        return row_widget, buttons

    def _build_setup_list_view(self) -> QWidget:
        root = QWidget()
        layout = QVBoxLayout(root)

        title = QLabel("Setups")
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(title)

        btn_row, buttons = self._build_header_buttons(include_import=True)
        layout.addWidget(btn_row)

        self.setup_list = QListWidget()
        layout.addWidget(self.setup_list)

        buttons["new"].clicked.connect(self._new_setup)
        buttons["delete"].clicked.connect(self._delete_setup)
        buttons["rename"].clicked.connect(self._rename_setup)
        buttons["import"].clicked.connect(self._import_dialog)
        buttons["export"].clicked.connect(self._export_selected_setup)

        self.setup_list.itemClicked.connect(self._setup_row_clicked)
        return root

    def _build_setup_editor_view(self) -> QWidget:
        root = QWidget()
        layout = QVBoxLayout(root)

        self.setup_editor_title = QLabel("Setup")
        self.setup_editor_title.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(self.setup_editor_title)

        btn_row, buttons = self._build_header_buttons(include_import=False)
        layout.addWidget(btn_row)

        self.macro_list = QListWidget()
        layout.addWidget(self.macro_list)

        back_btn = QPushButton("Back to Setups")
        back_btn.clicked.connect(self.show_setups_view)
        layout.addWidget(back_btn)

        buttons["new"].clicked.connect(self._new_macro)
        buttons["delete"].clicked.connect(self._delete_macro)
        buttons["rename"].clicked.connect(self._rename_macro)
        buttons["export"].clicked.connect(self._export_selected_setup)
        self.macro_list.itemClicked.connect(self._macro_clicked)
        return root

    def show_setups_view(self) -> None:
        self.stack.setCurrentWidget(self.setup_list_view)

    def show_setup_editor(self, index: int) -> None:
        if index < 0 or index >= len(self.store.setups):
            return
        self.current_setup_index = index
        self.setup_editor_title.setText(self.store.setups[index].name)
        self._refresh_macros(index)
        self.stack.setCurrentWidget(self.setup_editor_view)

    def _refresh_setups(self) -> None:
        self.store.ensure_single_active()
        self.setup_list.clear()
        for idx, setup in enumerate(self.store.setups):
            item = QListWidgetItem()
            item.setData(Qt.UserRole, idx)
            self.setup_list.addItem(item)
            widget = self._setup_row_widget(setup, idx)
            item.setSizeHint(widget.sizeHint())
            self.setup_list.setItemWidget(item, widget)

    def _setup_row_widget(self, setup: Setup, index: int) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(8, 8, 8, 8)

        checkbox = QPushButton("☑" if setup.active else "☐")
        checkbox.setFixedWidth(32)
        checkbox.clicked.connect(lambda: self._set_active_setup(index))

        text_col = QWidget()
        text_layout = QVBoxLayout(text_col)
        text_layout.setContentsMargins(0, 0, 0, 0)
        name_label = QLabel(setup.name)
        author_label = QLabel(setup.author)
        author_label.setStyleSheet("font-size: 11px; color: #777;")
        text_layout.addWidget(name_label)
        text_layout.addWidget(author_label)

        arrow = QLabel(">")
        arrow.setAlignment(Qt.AlignVCenter | Qt.AlignRight)

        layout.addWidget(checkbox)
        layout.addWidget(text_col, 1)
        layout.addWidget(arrow)
        return row

    def _refresh_macros(self, setup_index: int) -> None:
        self.macro_list.clear()
        setup = self.store.setups[setup_index]
        for idx, macro in enumerate(setup.macros):
            keybind = macro.keybind or ""
            item = QListWidgetItem(f"{keybind:<12} {macro.name}")
            item.setData(Qt.UserRole, idx)
            self.macro_list.addItem(item)

    def _selected_setup_index(self) -> int:
        item = self.setup_list.currentItem()
        if item is None:
            return -1
        return int(item.data(Qt.UserRole))

    def _new_setup(self) -> None:
        name, ok = QInputDialog.getText(self, "New Setup", "Setup name:")
        if not ok or not name.strip():
            return
        author = getpass.getuser() or "Unknown"
        self.store.setups.append(Setup(name=name.strip(), author=author, macros=[], active=False))
        self.store.ensure_single_active()
        self.store.save()
        self._refresh_setups()

    def _delete_setup(self) -> None:
        idx = self._selected_setup_index()
        if idx < 0 or idx >= len(self.store.setups):
            return
        self.store.setups.pop(idx)
        if not self.store.setups:
            self.store.setups.append(Setup(name="Default Setup", author="Unknown", macros=[], active=True))
        self.store.ensure_single_active()
        self.store.save()
        self._refresh_setups()

    def _rename_setup(self) -> None:
        idx = self._selected_setup_index()
        if idx < 0:
            return
        current = self.store.setups[idx].name
        name, ok = QInputDialog.getText(self, "Rename Setup", "Setup name:", text=current)
        if ok and name.strip():
            self.store.setups[idx].name = name.strip()
            self.store.save()
            self._refresh_setups()
            if self.current_setup_index == idx:
                self.setup_editor_title.setText(name.strip())

    def _set_active_setup(self, index: int) -> None:
        for i, setup in enumerate(self.store.setups):
            setup.active = i == index
        self.store.save()
        self._refresh_setups()

    def _setup_row_clicked(self, item: QListWidgetItem) -> None:
        idx = int(item.data(Qt.UserRole))
        self.show_setup_editor(idx)

    def _new_macro(self) -> None:
        if self.current_setup_index < 0:
            return
        name, ok = QInputDialog.getText(self, "New Macro", "Macro name:")
        if not ok or not name.strip():
            return
        macro = Macro(name=name.strip(), author=getpass.getuser() or "Unknown", keybind="", actions=[])
        self.store.setups[self.current_setup_index].macros.append(macro)
        self.store.save()
        self._refresh_macros(self.current_setup_index)

    def _delete_macro(self) -> None:
        if self.current_setup_index < 0:
            return
        row = self.macro_list.currentRow()
        setup = self.store.setups[self.current_setup_index]
        if row < 0 or row >= len(setup.macros):
            return
        setup.macros.pop(row)
        self.store.save()
        self._refresh_macros(self.current_setup_index)

    def _rename_macro(self) -> None:
        if self.current_setup_index < 0:
            return
        row = self.macro_list.currentRow()
        setup = self.store.setups[self.current_setup_index]
        if row < 0 or row >= len(setup.macros):
            return
        current = setup.macros[row].name
        name, ok = QInputDialog.getText(self, "Rename Macro", "Macro name:", text=current)
        if ok and name.strip():
            setup.macros[row].name = name.strip()
            self.store.save()
            self._refresh_macros(self.current_setup_index)

    def _macro_clicked(self, item: QListWidgetItem) -> None:
        if self.current_setup_index < 0:
            return
        idx = int(item.data(Qt.UserRole))
        setup = self.store.setups[self.current_setup_index]
        if idx < 0 or idx >= len(setup.macros):
            return
        editor = MacroEditorWindow(setup.macros[idx], self.store)
        editor.macro_saved.connect(lambda: self._refresh_macros(self.current_setup_index))
        editor.show()
        self._open_editors.append(editor)

    def _export_selected_setup(self) -> None:
        idx = self._selected_setup_index() if self.stack.currentWidget() is self.setup_list_view else self.current_setup_index
        if idx < 0 or idx >= len(self.store.setups):
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Setup", filter="automa Setup (*.ats)")
        if not file_path:
            return
        path = file_path if file_path.endswith(".ats") else f"{file_path}.ats"
        self.store.export_setup(self.store.setups[idx], Path(path))

    def _import_dialog(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Import", filter="automa files (*.ats *.atm)")
        if not file_path:
            return
        self._import_path(Path(file_path))

    def _import_path(self, path: Path) -> None:
        ext = path.suffix.lower()
        if ext == ".ats":
            self.store.import_setup(path)
            self._refresh_setups()
            return
        if ext == ".atm":
            macro = self.store.import_macro(path)
            setup_names = [s.name for s in self.store.setups]
            if not setup_names:
                self.store.setups.append(Setup(name="Default Setup", author="Unknown", macros=[], active=True))
                setup_names = [self.store.setups[0].name]
            setup_name, ok = QInputDialog.getItem(self, "Choose Setup", "Add macro to setup:", setup_names, 0, False)
            if not ok:
                return
            index = setup_names.index(setup_name)
            self.store.setups[index].macros.append(macro)
            self.store.save()
            self._refresh_setups()
            if self.current_setup_index == index:
                self._refresh_macros(index)
            return
        QMessageBox.warning(self, "Import", "Unsupported file type")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self._import_path(Path(url.toLocalFile()))
        event.acceptProposedAction()
