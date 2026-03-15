from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from automa.core.macro_store import MacroStore


class RobustnessTests(unittest.TestCase):
    def test_macro_store_recovers_from_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "macros.json"
            path.write_text("{invalid-json", encoding="utf-8")
            store = MacroStore(path)
            self.assertEqual(len(store.groups), 1)
            self.assertEqual(store.groups[0].name, "Default Setup")


if __name__ == "__main__":
    unittest.main()
