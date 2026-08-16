from __future__ import annotations

import ast
import unittest
from pathlib import Path


class BoundaryTests(unittest.TestCase):
    def test_core_does_not_import_agent_or_network_modules(self) -> None:
        source_root = Path(__file__).parents[1] / "src/ph_driver_impact"
        forbidden = {"ph_driver_impact_agent", "urllib", "http", "requests", "openai"}
        for path in source_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imports: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
            self.assertFalse(imports & forbidden, f"{path} imports {imports & forbidden}")


if __name__ == "__main__":
    unittest.main()
