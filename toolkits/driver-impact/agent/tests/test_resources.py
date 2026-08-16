from __future__ import annotations

import json
import unittest
from importlib.resources import files
from pathlib import Path

from ph_driver_impact.machine import validate_impact_document
from ph_driver_impact_agent.contracts import validate_agent_output


class ResourceTests(unittest.TestCase):
    def test_packaged_schemas_are_valid_json_and_closed(self) -> None:
        root = files("ph_driver_impact_agent.resources.schemas")
        for name in ("agent_output.schema.json", "task_packet.schema.json"):
            schema = json.loads(root.joinpath(name).read_text(encoding="utf-8"))
            self.assertFalse(schema.get("additionalProperties", False))

    def test_checked_in_examples_match_runtime_contracts(self) -> None:
        examples = Path(__file__).parents[2] / "examples"
        impact = json.loads((examples / "impact-transaction.json").read_text(encoding="utf-8"))
        output = json.loads(
            (examples / "agent-output-transaction.json").read_text(encoding="utf-8")
        )
        validate_impact_document(impact)
        validate_agent_output(output, impact)


if __name__ == "__main__":
    unittest.main()
