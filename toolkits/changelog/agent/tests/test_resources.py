from __future__ import annotations

import json
import unittest
from importlib.resources import files

from ph_changelog_agent.contracts import validate_agent_output, validate_facts


class ResourceTests(unittest.TestCase):
    def test_packaged_schemas_skill_and_examples_are_readable(self) -> None:
        resources = files("ph_changelog_agent").joinpath("resources")
        for relative in (
            ("schemas", "task_facts.schema.json"),
            ("schemas", "agent_output.schema.json"),
            ("skill", "SKILL.md"),
            ("skill", "STYLE.md"),
            ("skill", "examples", "01-fixed.md"),
            ("examples", "task-facts-seqring.json"),
            ("examples", "agent-output-seqring.json"),
        ):
            with self.subTest(resource=relative):
                resource = resources.joinpath(*relative)
                self.assertTrue(resource.is_file())
                self.assertTrue(resource.read_text(encoding="utf-8"))

    def test_packaged_json_examples_satisfy_runtime_contracts(self) -> None:
        examples = files("ph_changelog_agent").joinpath("resources", "examples")
        facts = json.loads(examples.joinpath("task-facts-seqring.json").read_text(encoding="utf-8"))
        output = json.loads(
            examples.joinpath("agent-output-seqring.json").read_text(encoding="utf-8")
        )
        validate_facts(facts)
        validate_agent_output(output, facts, {"Fixed"})

    def test_closed_authority_objects_match_packaged_schema(self) -> None:
        resource = files("ph_changelog_agent").joinpath(
            "resources", "schemas", "task_facts.schema.json"
        )
        schema = json.loads(resource.read_text(encoding="utf-8"))
        self.assertIs(schema["additionalProperties"], False)
        self.assertIs(schema["properties"]["change"]["additionalProperties"], False)
        self.assertIs(schema["properties"]["constraints"]["additionalProperties"], False)

    def test_output_schema_matches_runtime_entry_ceiling(self) -> None:
        resource = files("ph_changelog_agent").joinpath(
            "resources", "schemas", "agent_output.schema.json"
        )
        schema = json.loads(resource.read_text(encoding="utf-8"))
        ok_variant = next(
            variant
            for variant in schema["oneOf"]
            if variant["properties"]["status"].get("const") == "ok"
        )
        self.assertEqual(ok_variant["properties"]["entries"]["maxItems"], 8)


if __name__ == "__main__":
    unittest.main()
