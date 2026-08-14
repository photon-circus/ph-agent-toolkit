"""Handwritten validation for the changelog agent JSON contracts.

The package ships the corresponding JSON Schemas as documentation and for
consumers that already use a schema validator. Keeping runtime validation here
avoids adding a heavy dependency to a small local-agent adapter.
"""

from __future__ import annotations

from typing import Any


class ContractError(ValueError):
    """Raised when supervisor facts or model output violate their contract."""


# Backwards-friendly name used by the prototype.
FactsError = ContractError


def _is_integer(value: object) -> bool:
    # JSON Schema does not consider booleans integers, while Python does.
    return isinstance(value, int) and not isinstance(value, bool)


def _require_object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    return value


def _require_string(value: object, label: str, *, non_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ContractError(f"{label} must be a string")
    if non_empty and len(value) == 0:
        raise ContractError(f"{label} must be non-empty")
    return value


def _require_string_array(
    value: object,
    label: str,
    *,
    non_empty: bool = False,
    unique: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        raise ContractError(f"{label} must be an array")
    if non_empty and not value:
        raise ContractError(f"{label} must be a non-empty array")
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise ContractError(f"{label}[{index}] must be a string")
    if unique and len(set(value)) != len(value):
        raise ContractError(f"{label} must contain unique values")
    return value


def _reject_extra_fields(value: dict[str, Any], allowed: set[str], label: str) -> None:
    extras = sorted(set(value) - allowed)
    if extras:
        raise ContractError(f"{label} has unexpected field(s): {', '.join(extras)}")


def validate_facts(data: object) -> None:
    """Validate supervisor-provided ``TASK_FACTS``.

    Every object is closed so misspelled authority fields cannot silently fall
    back to a less restrictive default.
    """

    facts_document = _require_object(data, "task facts")
    required = {"schema_version", "task", "target", "facts", "target_sections", "constraints"}
    missing = sorted(required - set(facts_document))
    if missing:
        raise ContractError(f"missing required field(s): {', '.join(missing)}")
    _reject_extra_fields(
        facts_document,
        {
            "schema_version",
            "task",
            "target",
            "change",
            "facts",
            "target_sections",
            "allowed_claims",
            "forbidden_claims",
            "evidence",
            "constraints",
        },
        "task facts",
    )

    schema_version = facts_document["schema_version"]
    if not _is_integer(schema_version) or schema_version != 1:
        raise ContractError("schema_version must be the integer 1")
    if facts_document["task"] != "changelog_update" or not isinstance(facts_document["task"], str):
        raise ContractError("task must be 'changelog_update'")
    if facts_document["target"] != "Unreleased" or not isinstance(facts_document["target"], str):
        raise ContractError("target must be 'Unreleased'")

    raw_facts = facts_document["facts"]
    if not isinstance(raw_facts, list) or not raw_facts:
        raise ContractError("facts must be a non-empty array")
    seen_fact_ids: set[str] = set()
    for index, raw_fact in enumerate(raw_facts):
        fact = _require_object(raw_fact, f"facts[{index}]")
        missing_fact_fields = {"id", "text"} - set(fact)
        if missing_fact_fields:
            raise ContractError(
                f"facts[{index}] is missing field(s): {', '.join(sorted(missing_fact_fields))}"
            )
        _reject_extra_fields(fact, {"id", "text"}, f"facts[{index}]")
        fact_id = _require_string(fact["id"], f"facts[{index}].id", non_empty=True)
        _require_string(fact["text"], f"facts[{index}].text", non_empty=True)
        if fact_id in seen_fact_ids:
            raise ContractError(f"duplicate fact id: {fact_id}")
        seen_fact_ids.add(fact_id)

    _require_string_array(
        facts_document["target_sections"],
        "target_sections",
        non_empty=True,
        unique=True,
    )

    for field in ("allowed_claims", "forbidden_claims", "evidence"):
        if field in facts_document:
            _require_string_array(facts_document[field], field)

    if "change" in facts_document:
        change = _require_object(facts_document["change"], "change")
        _reject_extra_fields(
            change,
            {"component", "kind", "breaking", "public_behavior_changed"},
            "change",
        )
        for field in ("component", "kind"):
            if field in change:
                _require_string(change[field], f"change.{field}")
        for field in ("breaking", "public_behavior_changed"):
            if field in change and not isinstance(change[field], bool):
                raise ContractError(f"change.{field} must be a boolean")

    constraints = _require_object(facts_document["constraints"], "constraints")
    constraint_required = {"modify_released_history", "max_entries"}
    missing_constraints = sorted(constraint_required - set(constraints))
    if missing_constraints:
        raise ContractError(f"constraints is missing field(s): {', '.join(missing_constraints)}")
    _reject_extra_fields(
        constraints,
        {"modify_released_history", "max_entries"},
        "constraints",
    )
    if constraints["modify_released_history"] is not False:
        raise ContractError("constraints.modify_released_history must be false")
    max_entries = constraints["max_entries"]
    if not _is_integer(max_entries) or not 1 <= max_entries <= 8:
        raise ContractError("constraints.max_entries must be an integer from 1 through 8")


def validate_target_sections(facts: object, allowed_sections: set[str]) -> None:
    """Validate every supervisor-authorized section against the core profile."""

    validate_facts(facts)
    facts_document = _require_object(facts, "task facts")
    unknown = set(facts_document["target_sections"]) - allowed_sections
    if unknown:
        raise ContractError(
            "target_sections contains section(s) outside the selected profile: "
            + ", ".join(sorted(unknown))
        )


def validate_agent_output(
    output: object,
    facts: object,
    allowed_sections: set[str],
) -> None:
    """Validate model output and its authorization against ``TASK_FACTS``."""

    validate_target_sections(facts, allowed_sections)
    facts_document = _require_object(facts, "task facts")
    result = _require_object(output, "agent output")
    if "status" not in result:
        raise ContractError("agent output is missing field: status")
    status = result["status"]
    if status not in {"ok", "needs_supervisor"} or not isinstance(status, str):
        raise ContractError("agent output status must be 'ok' or 'needs_supervisor'")

    if status == "needs_supervisor":
        _reject_extra_fields(result, {"status", "reason"}, "needs_supervisor output")
        if "reason" not in result:
            raise ContractError("needs_supervisor output requires reason")
        _require_string(result["reason"], "reason", non_empty=True)
        return

    _reject_extra_fields(result, {"status", "entries"}, "ok output")
    if "entries" not in result:
        raise ContractError("ok output requires entries")
    entries = result["entries"]
    if not isinstance(entries, list) or not entries:
        raise ContractError("ok output requires a non-empty entries array")
    constraints = _require_object(facts_document["constraints"], "constraints")
    max_entries = constraints["max_entries"]
    if len(entries) > max_entries:
        raise ContractError(f"agent produced {len(entries)} entries; max_entries is {max_entries}")

    target_sections = set(facts_document["target_sections"])
    known_fact_ids = {fact["id"] for fact in facts_document["facts"]}
    forbidden_claims = facts_document.get("forbidden_claims", [])

    for index, raw_entry in enumerate(entries):
        entry = _require_object(raw_entry, f"entries[{index}]")
        required_entry_fields = {"section", "text", "fact_ids"}
        missing_entry_fields = sorted(required_entry_fields - set(entry))
        if missing_entry_fields:
            raise ContractError(
                f"entries[{index}] is missing field(s): {', '.join(missing_entry_fields)}"
            )
        _reject_extra_fields(entry, required_entry_fields, f"entries[{index}]")

        section = _require_string(entry["section"], f"entries[{index}].section")
        text = _require_string(entry["text"], f"entries[{index}].text", non_empty=True)
        fact_ids = _require_string_array(
            entry["fact_ids"],
            f"entries[{index}].fact_ids",
            non_empty=True,
            unique=True,
        )

        if section not in allowed_sections:
            raise ContractError(f"agent selected unknown section: {section}")
        if section not in target_sections:
            raise ContractError(f"agent selected section not authorized by supervisor: {section}")

        unknown = set(fact_ids) - known_fact_ids
        if unknown:
            raise ContractError(
                f"agent entry cites unknown fact id(s): {', '.join(sorted(unknown))}"
            )
        lowered_text = text.lower()
        for forbidden in forbidden_claims:
            if forbidden.lower() in lowered_text:
                raise ContractError(f"agent output contains forbidden claim/string: {forbidden!r}")
