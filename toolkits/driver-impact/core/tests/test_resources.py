from __future__ import annotations

import json
import unittest
from importlib.resources import files


class ResourceTests(unittest.TestCase):
    def test_machine_schema_and_profile_are_packaged(self) -> None:
        schema = json.loads(
            files("ph_driver_impact.resources.schemas")
            .joinpath("impact_document.schema.json")
            .read_text(encoding="utf-8")
        )
        profile = json.loads(
            files("ph_driver_impact.resources.profiles")
            .joinpath("photon-circus-driver-v1.json")
            .read_text(encoding="utf-8")
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(profile["name"], "photon-circus-driver-v1")


if __name__ == "__main__":
    unittest.main()
