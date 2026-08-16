from __future__ import annotations

import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from ph_driver_impact.git import GitError
from ph_driver_impact.inspect import InspectionError, StaleRepositoryError, inspect_repository
from ph_driver_impact.profile import load_profile


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class InspectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        git(self.root, "init")
        git(self.root, "config", "user.email", "test@example.invalid")
        git(self.root, "config", "user.name", "Test")
        (self.root / "docs").mkdir()
        (self.root / "crates/clock/src").mkdir(parents=True)
        (self.root / "AGENTS.md").write_text(
            "# Policy\n## Commands\n```bash\ncargo test --workspace\n```\n", encoding="utf-8"
        )
        (self.root / "docs/INVARIANTS.md").write_text(
            "# Invariants\n## Runtime\n### I-1 Exact traffic\n", encoding="utf-8"
        )
        (self.root / "docs/API_CONTRACT.md").write_text("# API\n## Driver\n", encoding="utf-8")
        (self.root / "docs/TEST_PLAN.md").write_text("# Tests\n## Level 2\n", encoding="utf-8")
        (self.root / "Cargo.toml").write_text(
            '[workspace]\nmembers = ["crates/clock"]\n', encoding="utf-8"
        )
        (self.root / "crates/clock/Cargo.toml").write_text(
            '[package]\nname = "ph-clock"\nversion = "0.1.0"\nedition = "2024"\n',
            encoding="utf-8",
        )
        self.driver = self.root / "crates/clock/src/driver.rs"
        self.driver.write_text("pub struct Driver;\n", encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "baseline")
        self.profile = load_profile()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_clean_worktree_is_clear(self) -> None:
        result = inspect_repository(self.root, self.profile)
        self.assertEqual(result["result"]["status"], "clear")
        self.assertEqual(result["changes"], [])
        self.assertTrue(
            any("no explicit stable semantic IDs" in item for item in result["warnings"])
        )

    def test_changed_driver_and_untracked_path_are_visible(self) -> None:
        self.driver.write_text("pub struct Driver { state: u8 }\n", encoding="utf-8")
        (self.root / "notes.bin").write_bytes(b"\x00\x01")
        result = inspect_repository(self.root, self.profile)
        self.assertEqual(result["result"]["status"], "review_required")
        paths = {change["path"] for change in result["changes"]}
        self.assertEqual(paths, {"crates/clock/src/driver.rs", "notes.bin"})
        driver = next(
            change for change in result["changes"] if change["path"].endswith("driver.rs")
        )
        self.assertIn("driver.transport", driver["rule_ids"])
        self.assertEqual(
            result["packages"], [{"name": "ph-clock", "manifest": "crates/clock/Cargo.toml"}]
        )
        self.assertTrue(result["unclassified"])
        self.assertIn("cargo test --workspace", result["suggested_commands"])
        self.assertTrue(
            any(item["kind"] == "transaction_test_review" for item in result["obligations"])
        )
        self.assertTrue(all(item["id"].startswith("A-") for item in result["authority_index"]))

    def test_staged_and_later_unstaged_bytes_are_both_reflected_by_target(self) -> None:
        self.driver.write_text("pub struct Driver(u8);\n", encoding="utf-8")
        git(self.root, "add", "crates/clock/src/driver.rs")
        self.driver.write_text("pub struct Driver(u16);\n", encoding="utf-8")
        result = inspect_repository(self.root, self.profile)
        self.assertIn("Driver(u16)", result["changes"][0]["patch"])
        self.assertNotIn("Driver(u8)", result["changes"][0]["patch"])

    def test_local_commit_to_commit_comparison(self) -> None:
        baseline = git(self.root, "rev-parse", "HEAD")
        self.driver.write_text("pub struct Driver { state: u8 }\n", encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "change")
        result = inspect_repository(self.root, self.profile, base=baseline, target="HEAD")
        self.assertEqual(len(result["changes"]), 1)
        self.assertEqual(result["snapshot"]["target"]["kind"], "commit")

    def test_output_path_can_be_excluded_from_untracked_inputs(self) -> None:
        (self.root / "impact.json").write_text("old report", encoding="utf-8")
        result = inspect_repository(self.root, self.profile, excluded_paths={"impact.json"})
        self.assertEqual(result["changes"], [])

    def test_rename_delete_and_untracked_unicode_are_reported(self) -> None:
        extra = self.root / "crates/clock/src/old.rs"
        deleted = self.root / "crates/clock/src/deleted.rs"
        extra.write_text("pub struct Old;\n", encoding="utf-8")
        deleted.write_text("pub struct Deleted;\n", encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "add files")
        git(self.root, "mv", "crates/clock/src/old.rs", "crates/clock/src/new.rs")
        deleted.unlink()
        (self.root / "naïve.txt").write_bytes(b"one\r\ntwo\r\n")
        result = inspect_repository(self.root, self.profile)
        statuses = {(item["path"], item["status"]) for item in result["changes"]}
        self.assertIn(("crates/clock/src/new.rs", "R"), statuses)
        self.assertIn(("crates/clock/src/deleted.rs", "D"), statuses)
        self.assertIn(("naïve.txt", "A"), statuses)

    def test_file_limit_refuses_oversized_input(self) -> None:
        self.driver.write_bytes(b"x" * 32)
        profile = replace(self.profile, limits={**self.profile.limits, "max_file_bytes": 16})
        with self.assertRaisesRegex(ValueError, "max_file_bytes"):
            inspect_repository(self.root, profile)

    def test_profile_path_traversal_is_refused(self) -> None:
        documents = ({"role": "escape", "path": "../secret.md", "required": True},)
        profile = replace(self.profile, documents=documents)
        with self.assertRaisesRegex(ValueError, "escapes repository root"):
            inspect_repository(self.root, profile)

    def test_stale_final_check_is_a_controlled_refusal(self) -> None:
        self.driver.write_text("pub struct Driver(u8);\n", encoding="utf-8")
        with patch(
            "ph_driver_impact.inspect.check_worktree_unchanged",
            side_effect=GitError("repository changed during inspection: src/driver.rs"),
        ):
            with self.assertRaises(StaleRepositoryError):
                inspect_repository(self.root, self.profile)

    def test_merge_conflict_is_refused(self) -> None:
        main_branch = git(self.root, "branch", "--show-current")
        git(self.root, "checkout", "-b", "other")
        self.driver.write_text("pub struct Other;\n", encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "other")
        git(self.root, "checkout", main_branch)
        self.driver.write_text("pub struct Main;\n", encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "main")
        subprocess.run(["git", "merge", "other"], cwd=self.root, capture_output=True)
        with self.assertRaisesRegex(InspectionError, "merge conflicts"):
            inspect_repository(self.root, self.profile)

    def test_changed_gitlink_remains_visible(self) -> None:
        first_target = git(self.root, "rev-parse", "HEAD")
        git(
            self.root,
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{first_target},vendor/device",
        )
        git(self.root, "commit", "-m", "add gitlink")
        baseline = git(self.root, "rev-parse", "HEAD")
        git(
            self.root,
            "update-index",
            "--cacheinfo",
            f"160000,{baseline},vendor/device",
        )
        git(self.root, "commit", "-m", "move gitlink")
        result = inspect_repository(self.root, self.profile, base=baseline, target="HEAD")
        self.assertEqual(
            [(item["path"], item["status"]) for item in result["changes"]], [("vendor/device", "M")]
        )
        self.assertEqual(result["unclassified"], ["C-001"])


if __name__ == "__main__":
    unittest.main()
