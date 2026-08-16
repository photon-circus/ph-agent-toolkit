"""Runtime validation for the versioned driver-impact machine document."""

from __future__ import annotations

from typing import Any


class MachineDocumentError(ValueError):
    """Raised when a driver-impact document violates its closed contract."""


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MachineDocumentError(f"{label} must be an object")
    return value


def _closed(value: dict[str, Any], required: set[str], label: str) -> None:
    missing = sorted(required - set(value))
    extra = sorted(set(value) - required)
    if missing:
        raise MachineDocumentError(f"{label} is missing field(s): {', '.join(missing)}")
    if extra:
        raise MachineDocumentError(f"{label} has unexpected field(s): {', '.join(extra)}")


def _string(value: object, label: str, *, non_empty: bool = True) -> str:
    if not isinstance(value, str) or (non_empty and not value):
        raise MachineDocumentError(f"{label} must be a non-empty string")
    return value


def _array(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise MachineDocumentError(f"{label} must be an array")
    return value


def _strings(value: object, label: str, *, unique: bool = False) -> list[str]:
    items = _array(value, label)
    for index, item in enumerate(items):
        _string(item, f"{label}[{index}]")
    if unique and len(items) != len(set(items)):
        raise MachineDocumentError(f"{label} must contain unique values")
    return items


def _optional_digest(value: object, label: str) -> None:
    if value is not None and (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise MachineDocumentError(f"{label} must be null or a lowercase SHA-256 digest")


def validate_impact_document(value: object) -> dict[str, Any]:
    """Validate and return a closed schema-version-1 impact document."""

    document = _object(value, "impact document")
    root_fields = {
        "schema_version",
        "task",
        "snapshot",
        "profile",
        "packages",
        "changes",
        "domains",
        "authority_index",
        "obligations",
        "unclassified",
        "ignored_paths",
        "suggested_commands",
        "warnings",
        "result",
    }
    _closed(document, root_fields, "impact document")
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise MachineDocumentError("schema_version must be the integer 1")
    if document["task"] != "driver_change_impact":
        raise MachineDocumentError("task must be 'driver_change_impact'")

    snapshot = _object(document["snapshot"], "snapshot")
    _closed(snapshot, {"repository", "base", "target"}, "snapshot")
    _string(snapshot["repository"], "snapshot.repository")
    base = _object(snapshot["base"], "snapshot.base")
    _closed(base, {"requested", "commit"}, "snapshot.base")
    _string(base["requested"], "snapshot.base.requested")
    _string(base["commit"], "snapshot.base.commit")
    target = _object(snapshot["target"], "snapshot.target")
    kind = target.get("kind")
    expected_target_fields = {"kind", "sha256"} if kind == "worktree" else {"kind", "commit"}
    _closed(target, expected_target_fields, "snapshot.target")
    if kind not in {"worktree", "commit"}:
        raise MachineDocumentError("snapshot.target.kind must be 'worktree' or 'commit'")
    identity_field = next(field for field in expected_target_fields if field != "kind")
    _string(target[identity_field], "snapshot target identity")
    if kind == "worktree":
        _optional_digest(target[identity_field], "snapshot.target.sha256")

    profile = _object(document["profile"], "profile")
    _closed(profile, {"name", "schema_version", "sha256"}, "profile")
    _string(profile["name"], "profile.name")
    if type(profile["schema_version"]) is not int or profile["schema_version"] != 1:
        raise MachineDocumentError("profile.schema_version must be the integer 1")
    _optional_digest(profile["sha256"], "profile.sha256")
    if profile["sha256"] is None:
        raise MachineDocumentError("profile.sha256 must not be null")

    for index, raw in enumerate(_array(document["packages"], "packages")):
        item = _object(raw, f"packages[{index}]")
        _closed(item, {"name", "manifest"}, f"packages[{index}]")
        _string(item["name"], f"packages[{index}].name")
        _string(item["manifest"], f"packages[{index}].manifest")

    change_ids: set[str] = set()
    change_fields = {
        "id",
        "path",
        "old_path",
        "status",
        "old_sha256",
        "new_sha256",
        "binary",
        "patch",
        "patch_truncated",
        "rule_ids",
        "domains",
    }
    for index, raw in enumerate(_array(document["changes"], "changes")):
        item = _object(raw, f"changes[{index}]")
        _closed(item, change_fields, f"changes[{index}]")
        identifier = _string(item["id"], f"changes[{index}].id")
        if identifier in change_ids:
            raise MachineDocumentError(f"duplicate change id: {identifier}")
        change_ids.add(identifier)
        _string(item["path"], f"changes[{index}].path")
        if item["old_path"] is not None:
            _string(item["old_path"], f"changes[{index}].old_path")
        if item["status"] not in {"A", "C", "D", "M", "R", "T", "U", "X", "B"}:
            raise MachineDocumentError(f"changes[{index}].status is unsupported")
        _optional_digest(item["old_sha256"], f"changes[{index}].old_sha256")
        _optional_digest(item["new_sha256"], f"changes[{index}].new_sha256")
        for field in ("binary", "patch_truncated"):
            if type(item[field]) is not bool:
                raise MachineDocumentError(f"changes[{index}].{field} must be a boolean")
        if not isinstance(item["patch"], str):
            raise MachineDocumentError(f"changes[{index}].patch must be a string")
        _strings(item["rule_ids"], f"changes[{index}].rule_ids", unique=True)
        _strings(item["domains"], f"changes[{index}].domains", unique=True)

    authority_ids: set[str] = set()
    authority_fields = {"id", "path", "kind", "heading_path", "text", "sha256", "line", "role"}
    for index, raw in enumerate(_array(document["authority_index"], "authority_index")):
        item = _object(raw, f"authority_index[{index}]")
        _closed(item, authority_fields, f"authority_index[{index}]")
        identifier = _string(item["id"], f"authority_index[{index}].id")
        if identifier in authority_ids:
            raise MachineDocumentError(f"duplicate authority id: {identifier}")
        authority_ids.add(identifier)
        for field in ("path", "text", "role"):
            _string(item[field], f"authority_index[{index}].{field}")
        if item["kind"] not in {"heading", "table_row"}:
            raise MachineDocumentError(f"authority_index[{index}].kind is unsupported")
        _optional_digest(item["sha256"], f"authority_index[{index}].sha256")
        if item["sha256"] is None:
            raise MachineDocumentError(f"authority_index[{index}].sha256 must not be null")
        _strings(item["heading_path"], f"authority_index[{index}].heading_path")
        if type(item["line"]) is not int or item["line"] < 1:
            raise MachineDocumentError(f"authority_index[{index}].line must be positive")

    obligation_ids: set[str] = set()
    obligation_fields = {
        "id",
        "kind",
        "strength",
        "reason",
        "rule_id",
        "change_refs",
        "authority_refs",
        "checks",
    }
    for index, raw in enumerate(_array(document["obligations"], "obligations")):
        item = _object(raw, f"obligations[{index}]")
        _closed(item, obligation_fields, f"obligations[{index}]")
        identifier = _string(item["id"], f"obligations[{index}].id")
        if identifier in obligation_ids:
            raise MachineDocumentError(f"duplicate obligation id: {identifier}")
        obligation_ids.add(identifier)
        for field in ("kind", "reason", "rule_id"):
            _string(item[field], f"obligations[{index}].{field}")
        if item["strength"] not in {
            "required",
            "candidate",
            "supervisor_decision",
            "informational",
        }:
            raise MachineDocumentError(f"obligations[{index}].strength is unsupported")
        refs = _strings(item["change_refs"], f"obligations[{index}].change_refs", unique=True)
        if not refs or not set(refs) <= change_ids:
            raise MachineDocumentError(
                f"obligations[{index}].change_refs contains unknown or no IDs"
            )
        refs = _strings(item["authority_refs"], f"obligations[{index}].authority_refs", unique=True)
        if not set(refs) <= authority_ids:
            raise MachineDocumentError(f"obligations[{index}].authority_refs contains unknown IDs")
        _strings(item["checks"], f"obligations[{index}].checks", unique=True)

    _strings(document["domains"], "domains", unique=True)
    unclassified = _strings(document["unclassified"], "unclassified", unique=True)
    if not set(unclassified) <= change_ids:
        raise MachineDocumentError("unclassified contains unknown change IDs")
    for field in ("ignored_paths", "suggested_commands"):
        _strings(document[field], field, unique=True)
    _strings(document["warnings"], "warnings")
    result = _object(document["result"], "result")
    _closed(result, {"status", "meaning"}, "result")
    if result["status"] not in {"clear", "review_required", "refused"}:
        raise MachineDocumentError("result.status is unsupported")
    _string(result["meaning"], "result.meaning")
    return document
