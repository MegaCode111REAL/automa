from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from automation_app.core.macro_store import MacroStore
from automation_app.gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    data_path = Path(__file__).resolve().parent / "data" / "macros.json"
    store = MacroStore(data_path)
    window = MainWindow(store=store)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
