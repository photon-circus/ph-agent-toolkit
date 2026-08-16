from __future__ import annotations

import unittest

from support import impact_document, ok_output

from ph_driver_impact_agent.contracts import ContractError, validate_agent_output


class ContractTests(unittest.TestCase):
    def test_accepts_grounded_output(self) -> None:
        self.assertEqual(validate_agent_output(ok_output(), impact_document())["status"], "ok")

    def test_rejects_invented_reference(self) -> None:
        output = ok_output()
        output["impacts"][0]["authority_refs"] = ["A-9999"]
        with self.assertRaisesRegex(ContractError, "unknown ID"):
            validate_agent_output(output, impact_document())

    def test_capability_claim_requires_supervisor(self) -> None:
        output = ok_output()
        output["impacts"][0]["kind"] = "capability_claim"
        with self.assertRaisesRegex(ContractError, "requires supervisor"):
            validate_agent_output(output, impact_document())

    def test_rejects_claim_that_tests_ran(self) -> None:
        output = ok_output()
        output["impacts"][0]["summary"] = "Tests passed for this change."
        with self.assertRaisesRegex(ContractError, "unsupported claim"):
            validate_agent_output(output, impact_document())

    def test_accepts_grounded_escalation(self) -> None:
        output = {
            "status": "needs_supervisor",
            "reason": "Ambiguous authority.",
            "change_refs": ["C-001"],
            "authority_refs": ["A-0001"],
        }
        self.assertEqual(
            validate_agent_output(output, impact_document())["status"], "needs_supervisor"
        )

    def test_unclassified_change_requires_escalation(self) -> None:
        impact = impact_document()
        impact["unclassified"] = ["C-001"]
        with self.assertRaisesRegex(ContractError, "unclassified"):
            validate_agent_output(ok_output(), impact)

    def test_supervisor_obligation_requires_escalation(self) -> None:
        impact = impact_document()
        impact["obligations"][0]["strength"] = "supervisor_decision"
        with self.assertRaisesRegex(ContractError, "supervisor_decision"):
            validate_agent_output(ok_output(), impact)

    def test_unknown_fields_are_rejected(self) -> None:
        output = ok_output()
        output["approved"] = True
        with self.assertRaisesRegex(ContractError, "unexpected field"):
            validate_agent_output(output, impact_document())


if __name__ == "__main__":
    unittest.main()
