from __future__ import annotations

import unittest

from support import impact_document

from ph_driver_impact_agent.packet import build_task_packet
from ph_driver_impact_agent.prompt import build_prompt


class PacketTests(unittest.TestCase):
    def test_packet_is_bounded_and_read_only(self) -> None:
        packet = build_task_packet(impact_document())
        self.assertEqual(packet["task"], "map_driver_change_impact")
        self.assertTrue(packet["constraints"]["read_only"])
        self.assertFalse(packet["constraints"]["checks_executed"])
        self.assertEqual([item["id"] for item in packet["authority"]], ["A-0001"])

    def test_prompt_contains_contract_and_packet(self) -> None:
        system, user = build_prompt(impact_document())
        self.assertIn("Return JSON only", system)
        self.assertIn('"C-001"', user)
        self.assertNotIn("cargo test", user)

    def test_large_patch_is_truncated_in_packet(self) -> None:
        impact = impact_document()
        impact["changes"][0]["patch"] = "x" * 100_000
        packet = build_task_packet(impact)
        self.assertEqual(len(packet["changes"][0]["patch"]), 12_000)
        self.assertTrue(packet["changes"][0]["patch_omitted"])


if __name__ == "__main__":
    unittest.main()
