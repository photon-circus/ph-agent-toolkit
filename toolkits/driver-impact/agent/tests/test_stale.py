from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from ph_driver_impact import inspect_repository, load_profile
from ph_driver_impact_agent.stale import StaleImpactError, verify_current


def git(root: Path, *arguments: str) -> None:
    subprocess.run(["git", *arguments], cwd=root, check=True, capture_output=True)


class StaleTests(unittest.TestCase):
    def test_changed_worktree_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            git(root, "init")
            git(root, "config", "user.email", "test@example.invalid")
            git(root, "config", "user.name", "Test")
            (root / "src").mkdir()
            driver = root / "src/driver.rs"
            driver.write_text("pub struct Driver;\n", encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-m", "base")
            driver.write_text("pub struct Driver(u8);\n", encoding="utf-8")
            impact = inspect_repository(root, load_profile())
            verify_current(impact)
            driver.write_text("pub struct Driver(u16);\n", encoding="utf-8")
            with self.assertRaisesRegex(StaleImpactError, "no longer matches"):
                verify_current(impact)


if __name__ == "__main__":
    unittest.main()
