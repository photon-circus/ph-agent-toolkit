from __future__ import annotations

import ast
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from ph_changelog.cli import main
from ph_changelog.merge import MergeConflict, merge_changelogs
from ph_changelog.operations import add_entry, normalize_unreleased
from ph_changelog.profile import Profile, load_profile
from ph_changelog.validate import validate_text

PROFILE = Profile.from_dict(
    {
        "name": "test",
        "allowed_sections": [
            "Added",
            "Changed",
            "Deprecated",
            "Fixed",
            "Removed",
            "Security",
            "Documentation",
            "Known issues",
        ],
        "strict_from_version": "0.3.0",
        "protect_released_history": True,
        "release_summary_prefix": "**What this release delivers.**",
        "require_release_summary": True,
    }
)

BASE = """# Changelog

All notable changes.

## Unreleased

## 0.3.0 - 2026-08-12

**What this release delivers.** Stable release.

### Added
- Added A.

### Fixed
- Fixed B.

### Known issues
- Known C.

## 0.2.0 - 2026-08-10

### Documentation
- Legacy docs.
### Added
- Legacy duplicate ordering.
### Added
- Another legacy subsection.
"""


class ValidationTests(unittest.TestCase):
    def test_current_style_and_legacy_grandfathering(self):
        self.assertEqual(validate_text(BASE, PROFILE), [])

    def test_rejects_out_of_order_unreleased(self):
        text = BASE.replace(
            "## Unreleased\n",
            "## Unreleased\n\n### Fixed\n- Fix.\n\n### Added\n- Add.\n",
        )
        codes = {issue.code for issue in validate_text(text, PROFILE)}
        self.assertIn("section.order", codes)

    def test_rejects_duplicate_strict_section(self):
        text = BASE.replace(
            "## Unreleased\n",
            "## Unreleased\n\n### Added\n- A.\n\n### Added\n- B.\n",
        )
        codes = {issue.code for issue in validate_text(text, PROFILE)}
        self.assertIn("section.duplicate", codes)

    def test_rejects_duplicate_normalized_entry(self):
        text = BASE.replace(
            "## Unreleased\n",
            "## Unreleased\n\n### Added\n- Same entry.\n- Same   entry.\n",
        )
        codes = {issue.code for issue in validate_text(text, PROFILE)}
        self.assertIn("entry.duplicate", codes)

    def test_accepts_bracketed_keep_a_changelog_headings(self):
        text = (
            BASE.replace("## Unreleased", "## [Unreleased]")
            .replace("## 0.3.0 - 2026-08-12", "## [0.3.0] - 2026-08-12")
            .replace("## 0.2.0 - 2026-08-10", "## [0.2.0] - 2026-08-10")
        )
        self.assertEqual(validate_text(text, PROFILE), [])

    def test_rejects_missing_heading_for_bullet(self):
        text = BASE.replace("## Unreleased\n", "## Unreleased\n\n- orphan entry\n")
        codes = {issue.code for issue in validate_text(text, PROFILE)}
        self.assertIn("unreleased.missing_section", codes)

    def test_ignores_release_and_section_headings_inside_fences(self):
        for marker in ("```", "~~~~"):
            with self.subTest(marker=marker):
                text = BASE.replace(
                    "## Unreleased\n",
                    "## Unreleased\n\n"
                    f"{marker}markdown\n"
                    "## Example release\n"
                    "### Example section\n"
                    f"{marker}\n\n"
                    "### Fixed\n"
                    "- A real fix.\n",
                )
                self.assertEqual(validate_text(text, PROFILE), [])

    def test_rejects_title_after_release_heading(self):
        text = "## Unreleased\n\n# Changelog\n"
        codes = {issue.code for issue in validate_text(text, PROFILE)}
        self.assertIn("title.order", codes)

    def test_required_section_policy_reports_missing_section(self):
        required = Profile.from_dict(
            {
                "name": "required-test",
                "allowed_sections": PROFILE.allowed_sections,
                "strict_from_version": "0.3.0",
                "required_unreleased_sections": ["Fixed"],
                "protect_released_history": True,
                "release_summary_prefix": "**What this release delivers.**",
                "require_release_summary": True,
            }
        )
        codes = {issue.code for issue in validate_text(BASE, required)}
        self.assertIn("section.missing", codes)

    def test_strict_release_requires_summary_prefix(self):
        text = BASE.replace("**What this release delivers.** Stable release.\n\n", "")
        codes = {issue.code for issue in validate_text(text, PROFILE)}
        self.assertIn("release.summary", codes)

    def test_history_protection_is_byte_exact(self):
        changed = BASE.replace("- Added A.", "- Added A changed.")
        codes = {issue.code for issue in validate_text(changed, PROFILE, base_text=BASE)}
        self.assertIn("history.modified", codes)


class OperationTests(unittest.TestCase):
    def test_add_creates_section_in_canonical_order(self):
        text = add_entry(BASE, PROFILE, "Fixed", "New fix.")
        self.assertIn("## Unreleased\n\n### Fixed\n- New fix.", text)
        self.assertEqual(validate_text(text, PROFILE), [])

    def test_add_multiple_sections_orders_them(self):
        text = add_entry(BASE, PROFILE, "Documentation", "Documented X.")
        text = add_entry(text, PROFILE, "Added", "Added X.")
        u = text.split("## 0.3.0", 1)[0]
        self.assertLess(u.index("### Added"), u.index("### Documentation"))

    def test_normalize_coalesces_duplicate_unreleased_sections(self):
        messy = BASE.replace(
            "## Unreleased\n",
            "## Unreleased\n\n### Added\n- A.\n\n### Fixed\n- F.\n\n### Added\n- B.\n",
        )
        normalized = normalize_unreleased(messy, PROFILE)
        u = normalized.split("## 0.3.0", 1)[0]
        self.assertEqual(u.count("### Added"), 1)
        self.assertIn("- A.", u)
        self.assertIn("- B.", u)
        self.assertEqual(validate_text(normalized, PROFILE), [])

    def test_normalize_unreleased_only(self):
        messy = BASE.replace(
            "## Unreleased\n",
            "## Unreleased\n\n### Documentation\n- D.\n\n### Added\n- A.\n",
        )
        normalized = normalize_unreleased(messy, PROFILE)
        u = normalized.split("## 0.3.0", 1)[0]
        self.assertLess(u.index("### Added"), u.index("### Documentation"))
        self.assertIn("### Documentation\n- Legacy docs.\n### Added", normalized)

    def test_crlf_render_does_not_double_carriage_returns(self):
        text = BASE.replace(
            "## Unreleased\n",
            "## Unreleased\n"
            "Narrative line one.\n"
            "Narrative line two.\n\n"
            "### Added\n"
            "- First entry.\n"
            "  Wrapped detail.\n"
            "- Second entry.\n",
        ).replace("\n", "\r\n")
        updated = add_entry(text, PROFILE, "Fixed", "A CRLF-safe fix.")
        unreleased = updated.split("## 0.3.0", 1)[0]
        self.assertNotIn("\r\r\n", unreleased)
        self.assertIn("Narrative line one.\r\nNarrative line two.", unreleased)
        self.assertIn("- First entry.\r\n  Wrapped detail.\r\n- Second entry.", unreleased)
        self.assertIn("### Fixed\r\n- A CRLF-safe fix.", unreleased)


class MergeTests(unittest.TestCase):
    def test_independent_sections_merge(self):
        ours = add_entry(BASE, PROFILE, "Added", "Added ours.")
        theirs = add_entry(BASE, PROFILE, "Fixed", "Fixed theirs.")
        merged = merge_changelogs(BASE, ours, theirs, PROFILE)
        self.assertIn("- Added ours.", merged)
        self.assertIn("- Fixed theirs.", merged)
        self.assertEqual(validate_text(merged, PROFILE, base_text=BASE), [])

    def test_same_section_additions_merge(self):
        ours = add_entry(BASE, PROFILE, "Fixed", "Fixed ours.")
        theirs = add_entry(BASE, PROFILE, "Fixed", "Fixed theirs.")
        merged = merge_changelogs(BASE, ours, theirs, PROFILE)
        self.assertIn("- Fixed ours.", merged)
        self.assertIn("- Fixed theirs.", merged)

    def test_history_change_conflicts(self):
        ours = BASE.replace("- Added A.", "- Changed released history.")
        with self.assertRaises(MergeConflict):
            merge_changelogs(BASE, ours, BASE, PROFILE)

    def test_edit_existing_unreleased_entry_conflicts(self):
        base = add_entry(BASE, PROFILE, "Fixed", "Existing fix.")
        ours = base.replace("Existing fix.", "Edited fix.")
        with self.assertRaises(MergeConflict):
            merge_changelogs(base, ours, base, PROFILE)

    def test_preamble_change_conflicts_instead_of_being_discarded(self):
        ours = BASE.replace("All notable changes.", "Changed preamble.")
        with self.assertRaises(MergeConflict):
            merge_changelogs(BASE, ours, BASE, PROFILE)

    def test_duplicate_branch_sections_conflict(self):
        ours = BASE.replace(
            "## Unreleased\n",
            "## Unreleased\n\n### Added\n- A.\n\n### Added\n- B.\n",
        )
        with self.assertRaises(MergeConflict):
            merge_changelogs(BASE, ours, BASE, PROFILE)


class PackagingAndCliTests(unittest.TestCase):
    def test_loads_bundled_profiles_by_name(self):
        self.assertEqual(load_profile("photon-circus").name, "photon-circus")
        self.assertEqual(load_profile("ph-eventing").name, "ph-eventing")

    def test_profile_rejects_unknown_and_mistyped_policy(self):
        for override in (
            {"allow_empty_unreleased": "false"},
            {"required_release_sections": "Fixed"},
            {"strict_from_version": 3},
            {"unknown_policy": True},
        ):
            with self.subTest(override=override):
                data = {"name": "invalid", "allowed_sections": ["Fixed"], **override}
                with self.assertRaises(ValueError):
                    Profile.from_dict(data)

    def test_cli_preserves_crlf_released_history_bytes(self):
        original = BASE.replace("\n", "\r\n").encode("utf-8")
        marker = b"## 0.3.0 - 2026-08-12"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CHANGELOG.md"
            path.write_bytes(original)
            result = main(
                [
                    "--profile",
                    "ph-eventing",
                    "add",
                    str(path),
                    "--section",
                    "Fixed",
                    "--entry",
                    "A Windows-safe change.",
                    "--write",
                ]
            )
            self.assertEqual(result, 0)
            updated = path.read_bytes()
            self.assertIn(b"## Unreleased\r\n\r\n### Fixed\r\n", updated)
            self.assertEqual(updated[updated.index(marker) :], original[original.index(marker) :])

    def test_core_has_no_agent_or_network_imports(self):
        source_root = Path(__file__).resolve().parents[1] / "src" / "ph_changelog"
        forbidden = {
            "http",
            "httpx",
            "openai",
            "ph_changelog_agent",
            "ph_changelog_remote",
            "requests",
            "urllib",
        }
        imported: set[str] = set()
        for path in source_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".", 1)[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".", 1)[0])
        self.assertEqual(imported & forbidden, set())

    def test_normalize_cli_refuses_invalid_result_without_writing(self):
        original = BASE.replace(
            "## Unreleased\n",
            "## Unreleased\n\n### Unsupported\n- Must not be written.\n",
        ).encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CHANGELOG.md"
            path.write_bytes(original)
            with contextlib.redirect_stderr(io.StringIO()):
                result = main(["--profile", "ph-eventing", "normalize", str(path), "--write"])
            self.assertEqual(result, 2)
            self.assertEqual(path.read_bytes(), original)

    def test_add_input_rejects_mistyped_boolean_without_writing(self):
        original = BASE.encode("utf-8")
        operation = {
            "section": "Fixed",
            "entry": "A fix that must not be marked breaking.",
            "breaking": "false",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CHANGELOG.md"
            input_path = Path(directory) / "operation.json"
            path.write_bytes(original)
            input_path.write_text(json.dumps(operation), encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                result = main(
                    [
                        "--profile",
                        "ph-eventing",
                        "add",
                        str(path),
                        "--input",
                        str(input_path),
                        "--write",
                    ]
                )
            self.assertEqual(result, 2)
            self.assertIn("breaking must be a boolean", stderr.getvalue())
            self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
