from __future__ import annotations

import argparse
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ph_changelog.profile import Profile
from ph_changelog_agent.apply import (
    StaleChangelogError,
    atomic_write_if_unchanged,
    read_changelog_snapshot,
)
from ph_changelog_agent.cli import cmd_run


class StaleSafeTests(unittest.TestCase):
    def test_atomic_write_replaces_unchanged_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CHANGELOG.md"
            path.write_bytes(b"old\n")
            snapshot = read_changelog_snapshot(path)
            atomic_write_if_unchanged(path, snapshot, "new\n")
            self.assertEqual(path.read_bytes(), b"new\n")
            self.assertEqual(list(path.parent.glob(f".{path.name}.*.tmp")), [])

    def test_stale_snapshot_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CHANGELOG.md"
            path.write_bytes(b"before model\n")
            snapshot = read_changelog_snapshot(path)
            path.write_bytes(b"edited during model\n")
            with self.assertRaises(StaleChangelogError):
                atomic_write_if_unchanged(path, snapshot, "model update\n")
            self.assertEqual(path.read_bytes(), b"edited during model\n")

    def test_cli_detects_an_edit_made_during_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CHANGELOG.md"
            path.write_text("# Changelog\n\n## Unreleased\n", encoding="utf-8")
            facts = {
                "schema_version": 1,
                "task": "changelog_update",
                "target": "Unreleased",
                "facts": [{"id": "F1", "text": "Polling is bounded."}],
                "target_sections": ["Fixed"],
                "constraints": {"modify_released_history": False, "max_entries": 1},
            }
            output = {
                "status": "ok",
                "entries": [
                    {
                        "section": "Fixed",
                        "text": "Polling is bounded.",
                        "fact_ids": ["F1"],
                    }
                ],
            }
            args = argparse.Namespace(
                profile="ignored",
                facts="ignored",
                path=str(path),
                skill_dir=None,
                model="coder",
                base_url=None,
                temperature=0.1,
                apply=True,
            )
            profile = Profile(name="test", allowed_sections=["Fixed"])

            def edit_during_generation(*_args, **_kwargs):
                path.write_text(
                    "# Changelog\n\n## Unreleased\n\n### Fixed\n- Concurrent edit.\n",
                    encoding="utf-8",
                )
                return output

            with (
                patch("ph_changelog_agent.cli.load_profile", return_value=profile),
                patch("ph_changelog_agent.cli._read_json", return_value=facts),
                patch(
                    "ph_changelog_agent.cli.generate_output",
                    side_effect=edit_during_generation,
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                with self.assertRaises(StaleChangelogError):
                    cmd_run(args)
            self.assertIn("Concurrent edit.", path.read_text(encoding="utf-8"))
            self.assertNotIn("Polling is bounded.", path.read_text(encoding="utf-8"))

    def test_needs_supervisor_exits_three_without_apply_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CHANGELOG.md"
            path.write_text("# Changelog\n\n## Unreleased\n", encoding="utf-8")
            args = argparse.Namespace(
                profile="ignored",
                facts="ignored",
                path=str(path),
                skill_dir=None,
                model="coder",
                base_url=None,
                temperature=0.1,
                apply=True,
            )
            facts = {
                "schema_version": 1,
                "task": "changelog_update",
                "target": "Unreleased",
                "facts": [{"id": "F1", "text": "Insufficient."}],
                "target_sections": ["Fixed"],
                "constraints": {"modify_released_history": False, "max_entries": 1},
            }
            profile = Profile(name="test", allowed_sections=["Fixed"])
            with (
                patch("ph_changelog_agent.cli.load_profile", return_value=profile),
                patch("ph_changelog_agent.cli._read_json", return_value=facts),
                patch(
                    "ph_changelog_agent.cli.generate_output",
                    return_value={
                        "status": "needs_supervisor",
                        "reason": "Need observable behavior.",
                    },
                ),
                patch("ph_changelog_agent.cli.apply_agent_output") as apply_output,
                patch("ph_changelog_agent.cli.atomic_write_if_unchanged") as atomic_write,
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    result = cmd_run(args)
            self.assertEqual(result, 3)
            apply_output.assert_not_called()
            atomic_write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
