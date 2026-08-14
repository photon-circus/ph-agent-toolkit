from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

from ph_changelog.profile import Profile
from ph_changelog_agent.cli import generate_output
from ph_changelog_agent.contracts import (
    ContractError,
    validate_agent_output,
    validate_facts,
    validate_target_sections,
)


def valid_facts() -> dict:
    return {
        "schema_version": 1,
        "task": "changelog_update",
        "target": "Unreleased",
        "change": {"breaking": False},
        "facts": [
            {"id": "F1", "text": "A behavior changed."},
            {"id": "F2", "text": "A test pins the new behavior."},
        ],
        "target_sections": ["Fixed"],
        "forbidden_claims": ["wait-free"],
        "constraints": {"modify_released_history": False, "max_entries": 2},
    }


class FactsContractTests(unittest.TestCase):
    def test_valid_facts(self) -> None:
        validate_facts(valid_facts())

    def test_requires_constraint_fields_and_bounded_integer(self) -> None:
        for invalid_max in (True, 0, 9, 1.5, "2"):
            with self.subTest(max_entries=invalid_max):
                facts = valid_facts()
                facts["constraints"]["max_entries"] = invalid_max
                with self.assertRaises(ContractError):
                    validate_facts(facts)

        facts = valid_facts()
        del facts["constraints"]["modify_released_history"]
        with self.assertRaises(ContractError):
            validate_facts(facts)

    def test_fact_objects_are_closed_and_ids_are_unique(self) -> None:
        facts = valid_facts()
        facts["facts"][0]["source"] = "guessed"
        with self.assertRaises(ContractError):
            validate_facts(facts)

        facts = valid_facts()
        facts["facts"][1]["id"] = "F1"
        with self.assertRaisesRegex(ContractError, "duplicate fact id"):
            validate_facts(facts)

    def test_target_sections_are_strings_and_unique(self) -> None:
        facts = valid_facts()
        facts["target_sections"] = ["Fixed", "Fixed"]
        with self.assertRaises(ContractError):
            validate_facts(facts)

    def test_authority_objects_are_closed(self) -> None:
        for field, value in (
            ("top", True),
            ("change", "unexpected"),
            ("constraints", 3),
        ):
            with self.subTest(field=field):
                facts = valid_facts()
                if field == "top":
                    facts["unexpected"] = value
                else:
                    facts[field]["unexpected"] = value
                with self.assertRaisesRegex(ContractError, "unexpected field"):
                    validate_facts(facts)

    def test_target_sections_must_exist_in_selected_profile(self) -> None:
        with self.assertRaisesRegex(ContractError, "outside the selected profile"):
            validate_target_sections(valid_facts(), {"Added"})


class AgentOutputContractTests(unittest.TestCase):
    def test_accepts_multiple_entries_in_one_authorized_section(self) -> None:
        output = {
            "status": "ok",
            "entries": [
                {"section": "Fixed", "text": "First.", "fact_ids": ["F1"]},
                {"section": "Fixed", "text": "Second.", "fact_ids": ["F2"]},
            ],
        }
        validate_agent_output(output, valid_facts(), {"Added", "Fixed"})

    def test_rejects_extra_output_fields(self) -> None:
        base = {
            "status": "ok",
            "entries": [{"section": "Fixed", "text": "Fixed.", "fact_ids": ["F1"]}],
        }
        for mutate in (
            lambda output: output.update({"reason": "also"}),
            lambda output: output["entries"][0].update({"confidence": 0.9}),
        ):
            with self.subTest(mutate=mutate):
                output = copy.deepcopy(base)
                mutate(output)
                with self.assertRaises(ContractError):
                    validate_agent_output(output, valid_facts(), {"Fixed"})

        with self.assertRaises(ContractError):
            validate_agent_output(
                {"status": "needs_supervisor", "reason": "Missing facts.", "entries": []},
                valid_facts(),
                {"Fixed"},
            )

    def test_rejects_duplicate_or_unknown_cited_fact_ids(self) -> None:
        for fact_ids in (["F1", "F1"], ["F3"]):
            with self.subTest(fact_ids=fact_ids):
                output = {
                    "status": "ok",
                    "entries": [{"section": "Fixed", "text": "Fixed.", "fact_ids": fact_ids}],
                }
                with self.assertRaises(ContractError):
                    validate_agent_output(output, valid_facts(), {"Fixed"})

    def test_rejects_forbidden_claim_and_entry_overflow(self) -> None:
        facts = valid_facts()
        facts["constraints"]["max_entries"] = 1
        with self.assertRaises(ContractError):
            validate_agent_output(
                {
                    "status": "ok",
                    "entries": [
                        {"section": "Fixed", "text": "One.", "fact_ids": ["F1"]},
                        {"section": "Fixed", "text": "Two.", "fact_ids": ["F2"]},
                    ],
                },
                facts,
                {"Fixed"},
            )
        with self.assertRaisesRegex(ContractError, "forbidden"):
            validate_agent_output(
                {
                    "status": "ok",
                    "entries": [
                        {
                            "section": "Fixed",
                            "text": "The operation is wait-free.",
                            "fact_ids": ["F1"],
                        }
                    ],
                },
                valid_facts(),
                {"Fixed"},
            )

    def test_invalid_target_section_fails_before_model_call(self) -> None:
        facts = valid_facts()
        facts["target_sections"] = ["Unknown"]
        profile = Profile(name="test", allowed_sections=["Fixed"])
        with patch("ph_changelog_agent.cli.call_lm_studio") as model_call:
            with self.assertRaisesRegex(ContractError, "outside the selected profile"):
                generate_output(facts, "# Changelog\n\n## Unreleased\n", profile)
        model_call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
