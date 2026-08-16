"""Closed validation for bounded semantic-impact output."""

from __future__ import annotations

from typing import Any

from ph_driver_impact.machine import validate_impact_document


class ContractError(ValueError):
    """Raised when an agent input or output violates its contract."""


IMPACT_KINDS = {
    "hardware_behavior",
    "public_api",
    "transaction_order",
    "error_surface",
    "test_coverage",
    "behavioral_model",
    "hil_evidence",
    "capability_claim",
    "documentation",
    "dependency",
    "unknown",
}
_FORBIDDEN_UNVERIFIED = (
    "all tests pass",
    "checks are green",
    "checks passed",
    "hardware support is proven",
    "test suite passes",
    "tests passed",
    "verified by running",
    "promote to supported",
    "promote to qualified",
    "is hardware-qualified",
)


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    return value


def _closed(value: dict[str, Any], fields: set[str], label: str) -> None:
    missing = sorted(fields - set(value))
    extra = sorted(set(value) - fields)
    if missing:
        raise ContractError(f"{label} is missing field(s): {', '.join(missing)}")
    if extra:
        raise ContractError(f"{label} has unexpected field(s): {', '.join(extra)}")


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value


def _refs(value: object, label: str, known: set[str], *, required: bool = True) -> list[str]:
    if not isinstance(value, list) or (required and not value):
        raise ContractError(f"{label} must be {'a non-empty' if required else 'an'} array")
    if any(not isinstance(item, str) for item in value):
        raise ContractError(f"{label} entries must be strings")
    if len(value) != len(set(value)):
        raise ContractError(f"{label} entries must be unique")
    unknown = set(value) - known
    if unknown:
        raise ContractError(f"{label} cites unknown ID(s): {', '.join(sorted(unknown))}")
    return value


def validate_agent_output(output: object, impact: object) -> dict[str, Any]:
    """Validate semantic output against exact IDs supplied by the core."""

    try:
        document = validate_impact_document(impact)
    except ValueError as error:
        raise ContractError(f"invalid impact document: {error}") from error
    result = _object(output, "agent output")
    status = result.get("status")
    if status == "needs_supervisor":
        _closed(result, {"status", "reason", "change_refs", "authority_refs"}, "agent output")
        _string(result["reason"], "reason")
        _refs(result["change_refs"], "change_refs", {item["id"] for item in document["changes"]})
        _refs(
            result["authority_refs"],
            "authority_refs",
            {item["id"] for item in document["authority_index"]},
            required=False,
        )
        return result
    if status != "ok":
        raise ContractError("agent output status must be 'ok' or 'needs_supervisor'")
    if document["unclassified"]:
        raise ContractError("unclassified changes require needs_supervisor output")
    if any(item["strength"] == "supervisor_decision" for item in document["obligations"]):
        raise ContractError("supervisor_decision obligations require needs_supervisor output")
    _closed(result, {"status", "impacts", "unresolved"}, "agent output")
    impacts = result["impacts"]
    if not isinstance(impacts, list) or not impacts:
        raise ContractError("ok output requires a non-empty impacts array")
    if not isinstance(result["unresolved"], list) or any(
        not isinstance(item, str) or not item.strip() for item in result["unresolved"]
    ):
        raise ContractError("unresolved must be an array of non-empty strings")
    if result["unresolved"]:
        raise ContractError("unresolved questions require needs_supervisor output")

    known_changes = {item["id"] for item in document["changes"]}
    known_authority = {item["id"] for item in document["authority_index"]}
    known_obligations = {item["id"] for item in document["obligations"]}
    fields = {
        "kind",
        "summary",
        "change_refs",
        "authority_refs",
        "obligation_refs",
        "recommended_action",
        "confidence",
        "requires_supervisor",
    }
    for index, raw in enumerate(impacts):
        item = _object(raw, f"impacts[{index}]")
        _closed(item, fields, f"impacts[{index}]")
        if item["kind"] not in IMPACT_KINDS:
            raise ContractError(f"impacts[{index}].kind is unsupported")
        summary = _string(item["summary"], f"impacts[{index}].summary")
        action = _string(item["recommended_action"], f"impacts[{index}].recommended_action")
        _refs(item["change_refs"], f"impacts[{index}].change_refs", known_changes)
        _refs(item["authority_refs"], f"impacts[{index}].authority_refs", known_authority)
        _refs(item["obligation_refs"], f"impacts[{index}].obligation_refs", known_obligations)
        if item["confidence"] not in {"high", "medium", "low"}:
            raise ContractError(f"impacts[{index}].confidence is unsupported")
        if type(item["requires_supervisor"]) is not bool:
            raise ContractError(f"impacts[{index}].requires_supervisor must be a boolean")
        if item["requires_supervisor"]:
            raise ContractError(f"impacts[{index}] requires needs_supervisor output")
        if (
            item["kind"] in {"hil_evidence", "capability_claim", "unknown"}
            and not item["requires_supervisor"]
        ):
            raise ContractError(f"impacts[{index}] kind requires supervisor review")
        lowered = f"{summary}\n{action}".lower()
        for forbidden in _FORBIDDEN_UNVERIFIED:
            if forbidden in lowered:
                raise ContractError(f"impacts[{index}] contains unsupported claim: {forbidden!r}")
    return result
