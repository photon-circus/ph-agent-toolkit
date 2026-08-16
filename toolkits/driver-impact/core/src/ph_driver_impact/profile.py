"""Closed profile loading for driver-impact policy."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ImpactProfile:
    """Validated impact profile data."""

    name: str
    sha256: str
    documents: tuple[dict[str, Any], ...]
    ignored: tuple[str, ...]
    rules: tuple[dict[str, Any], ...]
    limits: dict[str, int]


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _closed(value: dict[str, Any], allowed: set[str], label: str) -> None:
    extra = sorted(set(value) - allowed)
    if extra:
        raise ValueError(f"{label} has unexpected field(s): {', '.join(extra)}")


def _strings(value: object, label: str, *, non_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or (non_empty and not value):
        qualifier = "a non-empty" if non_empty else "an"
        raise ValueError(f"{label} must be {qualifier} array")
    if any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{label} entries must be non-empty strings")
    if len(set(value)) != len(value):
        raise ValueError(f"{label} entries must be unique")
    return tuple(value)


def validate_profile(data: object) -> ImpactProfile:
    raw = _object(data, "profile")
    _closed(raw, {"schema_version", "name", "documents", "ignored", "rules", "limits"}, "profile")
    required = {"schema_version", "name", "documents", "ignored", "rules", "limits"}
    missing = sorted(required - set(raw))
    if missing:
        raise ValueError(f"profile is missing field(s): {', '.join(missing)}")
    if type(raw["schema_version"]) is not int or raw["schema_version"] != 1:
        raise ValueError("profile.schema_version must be the integer 1")
    if not isinstance(raw["name"], str) or not raw["name"]:
        raise ValueError("profile.name must be a non-empty string")

    documents = raw["documents"]
    if not isinstance(documents, list) or not documents:
        raise ValueError("profile.documents must be a non-empty array")
    checked_documents: list[dict[str, Any]] = []
    roles: set[str] = set()
    for index, item in enumerate(documents):
        document = _object(item, f"documents[{index}]")
        _closed(document, {"role", "path", "required", "stable_ids"}, f"documents[{index}]")
        if not {"role", "path", "required"} <= set(document):
            raise ValueError(f"documents[{index}] must contain role, path, and required")
        if any(not isinstance(document[key], str) or not document[key] for key in ("role", "path")):
            raise ValueError(f"documents[{index}] role and path must be non-empty strings")
        if type(document["required"]) is not bool:
            raise ValueError(f"documents[{index}].required must be a boolean")
        if "stable_ids" in document and type(document["stable_ids"]) is not bool:
            raise ValueError(f"documents[{index}].stable_ids must be a boolean")
        if document["role"] in roles:
            raise ValueError(f"duplicate document role: {document['role']}")
        roles.add(document["role"])
        checked_documents.append(document)

    rules = raw["rules"]
    if not isinstance(rules, list) or not rules:
        raise ValueError("profile.rules must be a non-empty array")
    checked_rules: list[dict[str, Any]] = []
    rule_ids: set[str] = set()
    allowed_strengths = {"required", "candidate", "supervisor_decision", "informational"}
    for index, item in enumerate(rules):
        rule = _object(item, f"rules[{index}]")
        allowed = {"id", "globs", "domains", "obligations"}
        _closed(rule, allowed, f"rules[{index}]")
        if set(rule) != allowed:
            raise ValueError(f"rules[{index}] must contain id, globs, domains, and obligations")
        if not isinstance(rule["id"], str) or not rule["id"]:
            raise ValueError(f"rules[{index}].id must be a non-empty string")
        if rule["id"] in rule_ids:
            raise ValueError(f"duplicate rule id: {rule['id']}")
        rule_ids.add(rule["id"])
        _strings(rule["globs"], f"rules[{index}].globs", non_empty=True)
        _strings(rule["domains"], f"rules[{index}].domains", non_empty=True)
        obligations = rule["obligations"]
        if not isinstance(obligations, list):
            raise ValueError(f"rules[{index}].obligations must be an array")
        for obligation_index, raw_obligation in enumerate(obligations):
            label = f"rules[{index}].obligations[{obligation_index}]"
            obligation = _object(raw_obligation, label)
            obligation_keys = {"kind", "strength", "reason", "authority_roles", "checks"}
            _closed(obligation, obligation_keys, label)
            if set(obligation) != obligation_keys:
                raise ValueError(f"{label} must contain all obligation fields")
            for key in ("kind", "strength", "reason"):
                if not isinstance(obligation[key], str) or not obligation[key]:
                    raise ValueError(f"{label}.{key} must be a non-empty string")
            if obligation["strength"] not in allowed_strengths:
                raise ValueError(f"{label}.strength is unsupported")
            authority_roles = _strings(obligation["authority_roles"], f"{label}.authority_roles")
            unknown_roles = set(authority_roles) - roles
            if unknown_roles:
                raise ValueError(
                    f"{label} has unknown authority role(s): {', '.join(sorted(unknown_roles))}"
                )
            _strings(obligation["checks"], f"{label}.checks")
        checked_rules.append(rule)

    limits = _object(raw["limits"], "profile.limits")
    limit_keys = {
        "max_files",
        "max_diff_bytes",
        "max_file_bytes",
        "max_authority_entries",
        "max_authority_text",
    }
    _closed(limits, limit_keys, "profile.limits")
    if set(limits) != limit_keys:
        raise ValueError("profile.limits must contain every supported limit")
    if any(type(value) is not int or value < 1 for value in limits.values()):
        raise ValueError("profile limits must be positive integers")

    return ImpactProfile(
        name=raw["name"],
        sha256=hashlib.sha256(
            json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
                "utf-8"
            )
        ).hexdigest(),
        documents=tuple(checked_documents),
        ignored=_strings(raw["ignored"], "profile.ignored"),
        rules=tuple(checked_rules),
        limits=dict(limits),
    )


def load_profile(name_or_path: str = "photon-circus-driver-v1") -> ImpactProfile:
    path = Path(name_or_path)
    if path.is_file():
        raw = path.read_bytes()
    else:
        resource = files("ph_driver_impact.resources.profiles").joinpath(f"{name_or_path}.json")
        if not resource.is_file():
            raise ValueError(f"unknown driver-impact profile: {name_or_path}")
        raw = resource.read_bytes()
    return validate_profile(json.loads(raw.decode("utf-8")))
