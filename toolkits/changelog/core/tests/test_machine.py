from __future__ import annotations

import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from importlib.resources import files
from pathlib import Path
from unittest.mock import patch

from ph_changelog.cli import main
from ph_changelog.machine import deconstruct_changelog, render_machine_json
from ph_changelog.profile import load_profile

PROFILE = load_profile("photon-circus")
VALID_RAW = (
    "\ufeff# Changelog\r\n"
    "\r\n"
    "All notable changes.\r\n"
    "\r\n"
    "## [Unreleased]\r\n"
    "\r\n"
    "### Added\r\n"
    "- Add café support.\r\n"
    "  Preserve wrapped detail.\r\n"
    "\r\n"
    "## [1.0.0] - 2026-08-14\r\n"
    "\r\n"
    "### Fixed\r\n"
    "- Fix a released behavior.\r\n"
).encode("utf-8")


class _BinaryStdin:
    def __init__(self, raw: bytes) -> None:
        self.buffer = io.BytesIO(raw)


class MachineDocumentTests(unittest.TestCase):
    def test_deconstructs_lossless_artifact_and_semantic_entries(self) -> None:
        machine = deconstruct_changelog(
            VALID_RAW,
            PROFILE,
            {"kind": "file", "path": "CHANGELOG.md"},
        )

        self.assertEqual(machine["format"], "ph-changelog-document")
        self.assertEqual(machine["schema_version"], 1)
        self.assertEqual(machine["artifact"]["byte_length"], len(VALID_RAW))
        self.assertEqual(machine["artifact"]["sha256"], hashlib.sha256(VALID_RAW).hexdigest())
        self.assertTrue(machine["artifact"]["utf8_bom"])
        self.assertEqual(machine["artifact"]["raw_text"].encode("utf-8"), VALID_RAW)
        self.assertTrue(machine["validation"]["valid"])

        document = machine["document"]
        self.assertIsNotNone(document)
        self.assertFalse(document["preamble"].startswith("\ufeff"))
        unreleased = document["releases"][0]
        self.assertEqual(unreleased["kind"], "unreleased")
        entry = unreleased["sections"][0]["entries"][0]
        self.assertEqual(entry["markdown"], "- Add café support.\n  Preserve wrapped detail.")
        self.assertEqual(entry["text"], "Add café support.\nPreserve wrapped detail.")
        released = document["releases"][1]
        self.assertEqual(released["kind"], "release")
        self.assertEqual(released["version"], "1.0.0")

    def test_parse_failure_is_machine_readable(self) -> None:
        machine = deconstruct_changelog(b"not a changelog\n", PROFILE, {"kind": "stdin"})
        self.assertIsNone(machine["document"])
        self.assertFalse(machine["validation"]["valid"])
        codes = {issue["code"] for issue in machine["validation"]["issues"]}
        self.assertIn("parse", codes)

    def test_invalid_release_heading_does_not_leak_internal_sentinel(self) -> None:
        raw = b"# Changelog\n\n## Unreleased\n\n## next release\n"
        machine = deconstruct_changelog(raw, PROFILE, {"kind": "stdin"})
        invalid = machine["document"]["releases"][1]
        self.assertEqual(invalid["kind"], "invalid")
        self.assertIsNone(invalid["version"])
        self.assertNotIn("__INVALID__", render_machine_json(machine))

    def test_fenced_example_headings_do_not_corrupt_semantic_tree(self) -> None:
        raw = (
            b"# Changelog\n\n"
            b"## Unreleased\n\n"
            b"```markdown\n"
            b"## Example release\n"
            b"### Example section\n"
            b"```\n\n"
            b"### Fixed\n"
            b"- A real fix.\n"
        )
        machine = deconstruct_changelog(raw, PROFILE, {"kind": "stdin"})
        self.assertTrue(machine["validation"]["valid"])
        releases = machine["document"]["releases"]
        self.assertEqual(len(releases), 1)
        self.assertEqual([section["name"] for section in releases[0]["sections"]], ["Fixed"])

    def test_backtick_in_info_string_does_not_open_a_fence(self) -> None:
        raw = b"# Changelog\n\n```lang`invalid\n## Unreleased\n\n### Fixed\n- A real fix.\n"
        machine = deconstruct_changelog(raw, PROFILE, {"kind": "stdin"})
        self.assertTrue(machine["validation"]["valid"])
        releases = machine["document"]["releases"]
        self.assertEqual(len(releases), 1)
        self.assertEqual(releases[0]["kind"], "unreleased")

    def test_html_comment_template_headings_are_not_semantic(self) -> None:
        raw = (
            b"# Changelog\n\n"
            b"<!--\n"
            b"## Unreleased\n"
            b"### Added\n"
            b"- Template only.\n"
            b"-->\n\n"
            b"<!-- one-line template comment -->\n\n"
            b"## Unreleased\n\n"
            b"### Fixed\n"
            b"- A real fix.\n"
        )
        machine = deconstruct_changelog(raw, PROFILE, {"kind": "stdin"})
        self.assertTrue(machine["validation"]["valid"])
        releases = machine["document"]["releases"]
        self.assertEqual(len(releases), 1)
        self.assertEqual([section["name"] for section in releases[0]["sections"]], ["Fixed"])

    def test_rendering_is_stable_and_utf8_friendly(self) -> None:
        machine = deconstruct_changelog(VALID_RAW, PROFILE, {"kind": "stdin"})
        first = render_machine_json(machine)
        second = render_machine_json(machine)
        self.assertEqual(first, second)
        self.assertIn("café", first)
        self.assertTrue(first.endswith("\n"))

    def test_machine_source_objects_fail_closed(self) -> None:
        for source in (
            {"kind": "stdin", "path": "unexpected"},
            {"kind": "file"},
            {"kind": "http", "requested_url": "https://example.test"},
            {
                "kind": "http",
                "requested_url": "https://example.test/CHANGELOG.md",
                "final_url": "https://example.test/CHANGELOG.md",
                "query_redacted": False,
                "status": 206,
                "content_type": "text/plain",
                "etag": None,
                "last_modified": None,
            },
            {"kind": "unknown"},
        ):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    deconstruct_changelog(VALID_RAW, PROFILE, source)

    def test_packaged_schema_is_closed_and_versioned(self) -> None:
        resource = files("ph_changelog").joinpath("schemas", "changelog_document.schema.json")
        schema = json.loads(resource.read_text(encoding="utf-8"))
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        http_source = next(
            variant
            for variant in schema["properties"]["source"]["oneOf"]
            if variant["properties"]["kind"].get("const") == "http"
        )
        self.assertEqual(http_source["properties"]["status"]["const"], 200)
        for definition in schema["$defs"].values():
            self.assertIs(definition["additionalProperties"], False)


class InspectCliTests(unittest.TestCase):
    def test_inspect_file_writes_json_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            changelog = Path(directory) / "CHANGELOG.md"
            output = Path(directory) / "changelog.json"
            changelog.write_bytes(VALID_RAW)
            result = main(["inspect", str(changelog), "--output", str(output)])
            self.assertEqual(result, 0)
            machine = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(machine["source"], {"kind": "file", "path": str(changelog)})
            self.assertTrue(machine["validation"]["valid"])

    def test_inspect_stdin_emits_json_and_invalid_content_exits_one(self) -> None:
        stdout = io.StringIO()
        with (
            patch("ph_changelog.cli.sys.stdin", _BinaryStdin(b"not a changelog\n")),
            contextlib.redirect_stdout(stdout),
        ):
            result = main(["inspect", "-"])
        self.assertEqual(result, 1)
        machine = json.loads(stdout.getvalue())
        self.assertEqual(machine["source"], {"kind": "stdin"})
        self.assertIsNone(machine["document"])

    def test_inspect_operational_failure_preserves_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            changelog = Path(directory) / "CHANGELOG.md"
            output = Path(directory) / "changelog.json"
            changelog.write_bytes(b"\xff")
            output.write_bytes(b"existing")
            with contextlib.redirect_stderr(io.StringIO()):
                result = main(["inspect", str(changelog), "--output", str(output)])
            self.assertEqual(result, 2)
            self.assertEqual(output.read_bytes(), b"existing")

    def test_inspect_refuses_to_overwrite_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            changelog = Path(directory) / "CHANGELOG.md"
            changelog.write_bytes(VALID_RAW)
            with contextlib.redirect_stderr(io.StringIO()):
                result = main(["inspect", str(changelog), "--output", str(changelog)])
            self.assertEqual(result, 2)
            self.assertEqual(changelog.read_bytes(), VALID_RAW)


if __name__ == "__main__":
    unittest.main()
