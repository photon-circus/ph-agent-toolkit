from __future__ import annotations

import unittest

from ph_changelog.profile import Profile
from ph_changelog_agent.apply import apply_agent_output

FACTS = {
    "schema_version": 1,
    "task": "changelog_update",
    "target": "Unreleased",
    "change": {"breaking": False},
    "facts": [{"id": "F1", "text": "Polling is now bounded per call."}],
    "target_sections": ["Fixed"],
    "constraints": {"modify_released_history": False, "max_entries": 1},
}


class ApplyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = Profile(name="test", allowed_sections=["Added", "Fixed"])

    def test_applies_through_core_and_preserves_history(self) -> None:
        original = (
            "# Changelog\n\n## Unreleased\n\n## 1.0.0 - 2025-01-01\n\n### Added\n- Historical.\n"
        )
        output = {
            "status": "ok",
            "entries": [
                {
                    "section": "Fixed",
                    "text": "Polling is now bounded per call.",
                    "fact_ids": ["F1"],
                }
            ],
        }
        updated = apply_agent_output(original, output, FACTS, self.profile)
        self.assertIn("### Fixed\n- Polling is now bounded per call.", updated)
        self.assertEqual(
            updated[updated.index("## 1.0.0") :],
            original[original.index("## 1.0.0") :],
        )

    def test_refuses_needs_supervisor_output(self) -> None:
        with self.assertRaisesRegex(ValueError, "requested supervisor"):
            apply_agent_output(
                "# Changelog\n\n## Unreleased\n",
                {"status": "needs_supervisor", "reason": "Need an observable effect."},
                FACTS,
                self.profile,
            )


if __name__ == "__main__":
    unittest.main()
