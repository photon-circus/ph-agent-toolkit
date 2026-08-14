from __future__ import annotations

import ast
import unittest
from pathlib import Path


class DependencyBoundaryTests(unittest.TestCase):
    def test_agent_does_not_import_remote_adapter(self) -> None:
        source_root = Path(__file__).resolve().parents[1] / "src" / "ph_changelog_agent"
        imported: set[str] = set()
        for path in source_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".", 1)[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".", 1)[0])
        self.assertNotIn("ph_changelog_remote", imported)


if __name__ == "__main__":
    unittest.main()
