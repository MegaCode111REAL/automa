from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from automa.core.macro_store import MacroStore
from automa.gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    data_path = Path(__file__).resolve().parent / "data" / "macros.json"
    store = MacroStore(data_path)
    window = MainWindow(store=store)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
