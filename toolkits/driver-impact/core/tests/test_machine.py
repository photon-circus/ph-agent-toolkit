from __future__ import annotations

import copy
import unittest

from ph_driver_impact.machine import MachineDocumentError, validate_impact_document


def minimal_document() -> dict[str, object]:
    return {
        "schema_version": 1,
        "task": "driver_change_impact",
        "snapshot": {
            "repository": "C:/repo",
            "base": {"requested": "HEAD", "commit": "a"},
            "target": {"kind": "commit", "commit": "b"},
        },
        "profile": {"name": "profile", "schema_version": 1, "sha256": "0" * 64},
        "packages": [],
        "changes": [],
        "domains": [],
        "authority_index": [],
        "obligations": [],
        "unclassified": [],
        "ignored_paths": [],
        "suggested_commands": [],
        "warnings": [],
        "result": {"status": "clear", "meaning": "no obligations"},
    }


class MachineTests(unittest.TestCase):
    def test_accepts_closed_document(self) -> None:
        self.assertEqual(validate_impact_document(minimal_document())["schema_version"], 1)

    def test_rejects_unknown_root_field(self) -> None:
        document = copy.deepcopy(minimal_document())
        document["approved"] = True
        with self.assertRaisesRegex(MachineDocumentError, "unexpected field"):
            validate_impact_document(document)

    def test_rejects_boolean_schema_version(self) -> None:
        document = minimal_document()
        document["schema_version"] = True
        with self.assertRaisesRegex(MachineDocumentError, "integer 1"):
            validate_impact_document(document)


if __name__ == "__main__":
    unittest.main()
