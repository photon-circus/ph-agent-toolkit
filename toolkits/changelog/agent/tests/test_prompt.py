from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ph_changelog_agent.prompt import build_prompt, load_skill_assets

CHANGELOG = "# Changelog\n\n## Unreleased\n\n### Fixed\n- Existing entry.\n"
FACTS = {
    "schema_version": 1,
    "task": "changelog_update",
    "target": "Unreleased",
    "facts": [{"id": "F1", "text": "Something changed."}],
    "target_sections": ["Fixed"],
    "constraints": {"modify_released_history": False, "max_entries": 1},
}


class PromptTests(unittest.TestCase):
    def test_bundled_skill_works_outside_project_working_directory(self) -> None:
        old_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            os.chdir(directory)
            try:
                system, user = build_prompt(FACTS, CHANGELOG)
            finally:
                os.chdir(old_cwd)
        self.assertIn("Photon Circus changelog prose", system)
        self.assertIn("Existing entry.", user)
        self.assertIn('"id": "F1"', user)
        self.assertIn("01-fixed.md", user)

    def test_explicit_skill_override_precedes_environment(self) -> None:
        with (
            tempfile.TemporaryDirectory() as explicit_dir,
            tempfile.TemporaryDirectory() as env_dir,
        ):
            for directory, label in ((explicit_dir, "EXPLICIT"), (env_dir, "ENV")):
                root = Path(directory)
                (root / "examples").mkdir()
                (root / "SKILL.md").write_text(label, encoding="utf-8")
                (root / "STYLE.md").write_text("STYLE", encoding="utf-8")
            with patch.dict(os.environ, {"PH_CHANGELOG_SKILL_DIR": env_dir}):
                assets = load_skill_assets(explicit_dir)
        self.assertEqual(assets.skill, "EXPLICIT")


if __name__ == "__main__":
    unittest.main()
