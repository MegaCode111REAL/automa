from __future__ import annotations

from pathlib import Path
import platform

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from automa.core.macro_engine import MacroEngine
from automa.core.macro_recorder import MacroRecorder
from automa.core.app_settings import AppSettings
from automa.core.macro_store import MacroStore
from automa.core.models import Macro, MacroGroup
from automa.core.trigger_system import TriggerSystem
from automa.gui.group_manager import GroupManager
from automa.gui.macro_editor import MacroEditor
from automa.modules.image_detection import ImageDetector


class MainWindow(QMainWindow):
    def __init__(self, store: MacroStore) -> None:
        super().__init__()
        self.setWindowTitle("automa")
        self.resize(1400, 800)
        self.store = store
        self.settings = AppSettings()

        self.engine = MacroEngine()
        self.recorder = MacroRecorder()
        self.trigger_system = TriggerSystem()
        self.image_detector = ImageDetector()

        self.group_manager = GroupManager()
        self.group_manager.setMaximumWidth(260)
        self.group_manager.group_selected.connect(self._on_group_selected)
        self.group_manager.create_group.connect(self._create_group)
        self.group_manager.delete_group.connect(self._delete_group)

        self.macro_list = QListWidget()
        self.macro_list.currentRowChanged.connect(self._on_macro_selected)

        self.editor = MacroEditor()
        self.editor.macro_changed.connect(self._persist)
        self.editor.actions_list.model().rowsMoved.connect(lambda *_: self.editor.commit_reorder())

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(200)

        center_layout = QVBoxLayout()
        center_layout.addWidget(QLabel("Macros"))
        center_layout.addWidget(self.macro_list)

        macro_buttons = QHBoxLayout()
        add_macro_btn = QPushButton("Add Macro")
        del_macro_btn = QPushButton("Delete Macro")
        add_macro_btn.clicked.connect(self._create_macro)
        del_macro_btn.clicked.connect(self._delete_macro)
        macro_buttons.addWidget(add_macro_btn)
        macro_buttons.addWidget(del_macro_btn)
        center_layout.addLayout(macro_buttons)

        center_widget = QWidget()
        center_widget.setLayout(center_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.group_manager)
        splitter.addWidget(center_widget)
        splitter.addWidget(self.editor)
        splitter.setSizes([200, 360, 800])

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.addWidget(splitter)
        root_layout.addWidget(QLabel("Console / Logs"))
        root_layout.addWidget(self.log_output)

        self.setCentralWidget(root)
        self._build_toolbar()
        self._refresh_group_list()
        self._show_first_launch_instructions()
        self._log("Application loaded")


    def _show_first_launch_instructions(self) -> None:
        if self.settings.get_bool("permissions_instructions_seen", default=False):
            return

        os_name = platform.system()
        details = {
            "Windows": (
                "Windows permissions setup:\n"
                "1) Start automa once as your normal user.\n"
                "2) If global hotkeys or recording fail, restart automa as Administrator.\n"
                "3) Allow desktop/input access if your security software prompts."
            ),
            "Linux": (
                "Linux permissions setup:\n"
                "1) X11 is recommended for global hooks and macro playback.\n"
                "2) On Wayland, keyboard/mouse hooks may be blocked by compositor policy.\n"
                "3) Ensure your user can access input devices and screen capture APIs."
            ),
            "Darwin": (
                "macOS permissions setup:\n"
                "1) Open System Settings → Privacy & Security.\n"
                "2) Enable automa in Accessibility.\n"
                "3) Enable automa in Input Monitoring.\n"
                "4) Enable automa in Screen Recording for image detection/screen capture.\n"
                "5) Restart automa after enabling permissions."
            ),
        }
        message = details.get(os_name, "Grant input and screen permissions required by your OS.")

        QMessageBox.information(
            self,
            "First launch: required permissions",
            "automa needs OS-level permissions for global hotkeys, input automation, "
            "and screen capture.\n\n" + message,
        )
        self.settings.set_bool("permissions_instructions_seen", True)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)

        record_btn = QPushButton("Record")
        stop_record_btn = QPushButton("Stop Rec")
        play_btn = QPushButton("Play")
        stop_btn = QPushButton("Stop")
        pause_btn = QPushButton("Pause/Resume")
        trigger_btn = QPushButton("Start Triggers")
        trigger_stop_btn = QPushButton("Stop Triggers")
        detect_btn = QPushButton("Detect Image")
        import_btn = QPushButton("Import")
        export_btn = QPushButton("Export")

        record_btn.clicked.connect(lambda: self.recorder.start(on_log=self._log))
        stop_record_btn.clicked.connect(self._stop_recording_into_selected_group)
        play_btn.clicked.connect(self._play_selected_macro)
        stop_btn.clicked.connect(self.engine.stop)
        pause_btn.clicked.connect(self._toggle_pause)
        trigger_btn.clicked.connect(self._start_triggers)
        trigger_stop_btn.clicked.connect(self.trigger_system.stop)
        detect_btn.clicked.connect(self._run_image_detection)
        import_btn.clicked.connect(self._import)
        export_btn.clicked.connect(self._export)

        for button in [
            record_btn,
            stop_record_btn,
            play_btn,
            stop_btn,
            pause_btn,
            trigger_btn,
            trigger_stop_btn,
            detect_btn,
            import_btn,
            export_btn,
        ]:
            toolbar.addWidget(button)

    def _refresh_group_list(self) -> None:
        self.group_manager.set_groups([group.name for group in self.store.groups])

    def _on_group_selected(self, index: int) -> None:
        self.macro_list.clear()
        if index < 0 or index >= len(self.store.groups):
            return
        group = self.store.groups[index]
        self.macro_list.addItems([macro.name for macro in group.macros])
        if group.macros:
            self.macro_list.setCurrentRow(0)

    def _on_macro_selected(self, index: int) -> None:
        group = self._current_group()
        if not group or index < 0 or index >= len(group.macros):
            self.editor.set_macro(None)
            return
        self.editor.set_macro(group.macros[index])

    def _create_group(self, name: str) -> None:
        self.store.groups.append(MacroGroup(name=name, macros=[]))
        self._persist()
        self._refresh_group_list()
        self._log(f"Added group: {name}")

    def _delete_group(self, index: int) -> None:
        if len(self.store.groups) <= 1 or index < 0:
            return
        name = self.store.groups[index].name
        self.store.groups.pop(index)
        self._persist()
        self._refresh_group_list()
        self._log(f"Deleted group: {name}")

    def _create_macro(self) -> None:
        group = self._current_group()
        if not group:
            return
        name, ok = QInputDialog.getText(self, "Create Macro", "Macro name:")
        if not (ok and name.strip()):
            return
        macro = Macro(name=name.strip(), actions=[])
        group.macros.append(macro)
        self._persist()
        self._on_group_selected(self.group_manager.list_widget.currentRow())
        self._log(f"Added macro: {name}")

    def _delete_macro(self) -> None:
        group = self._current_group()
        row = self.macro_list.currentRow()
        if not group or row < 0:
            return
        name = group.macros[row].name
        group.macros.pop(row)
        self._persist()
        self._on_group_selected(self.group_manager.list_widget.currentRow())
        self._log(f"Deleted macro: {name}")

    def _stop_recording_into_selected_group(self) -> None:
        group = self._current_group()
        if not group:
            return
        name, ok = QInputDialog.getText(self, "Stop Recording", "Macro name:", text="recorded_macro")
        if not ok:
            return
        macro = self.recorder.stop(macro_name=name, on_log=self._log)
        group.macros.append(macro)
        self._persist()
        self._on_group_selected(self.group_manager.list_widget.currentRow())

    def _play_selected_macro(self) -> None:
        macro = self._current_macro()
        if not macro:
            return
        self.engine.play(macro=macro, speed=1.0, loop=False, on_log=self._log)
        self._log(f"Playing macro: {macro.name}")

    def _toggle_pause(self) -> None:
        if self.engine.pause_event.is_set():
            self.engine.resume()
            self._log("Playback resumed")
        else:
            self.engine.pause()
            self._log("Playback paused")

    def _start_triggers(self) -> None:
        macros = [macro for group in self.store.groups for macro in group.macros if macro.trigger]
        self.trigger_system.start(macros=macros, on_trigger=lambda m: self.engine.play(m), on_log=self._log)
        self._log(f"Trigger system active for {len(macros)} macros")

    def _run_image_detection(self) -> None:
        template, _ = QFileDialog.getOpenFileName(self, "Select Template", filter="Images (*.png *.jpg *.jpeg)")
        if not template:
            return
        result = self.image_detector.find_best_match(Path(template), threshold=0.8)
        if not result:
            QMessageBox.information(self, "Image Detection", "No image match found.")
            return
        QMessageBox.information(
            self,
            "Image Detection",
            f"Match score {result.score:.2f} at center {result.center}",
        )

    def _import(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Macro Set", filter="JSON files (*.json)")
        if not file_path:
            return
        self.store.import_file(Path(file_path))
        self._refresh_group_list()
        self._log(f"Imported: {file_path}")

    def _export(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Macro Set", filter="JSON files (*.json)")
        if not file_path:
            return
        self.store.export_file(Path(file_path))
        self._log(f"Exported: {file_path}")

    def _persist(self) -> None:
        self.store.save()

    def _current_group(self) -> MacroGroup | None:
        index = self.group_manager.list_widget.currentRow()
        if index < 0 or index >= len(self.store.groups):
            return None
        return self.store.groups[index]

    def _current_macro(self) -> Macro | None:
        group = self._current_group()
        row = self.macro_list.currentRow()
        if not group or row < 0 or row >= len(group.macros):
            return None
        return group.macros[row]

    def _log(self, message: str) -> None:
        self.log_output.appendPlainText(message)
