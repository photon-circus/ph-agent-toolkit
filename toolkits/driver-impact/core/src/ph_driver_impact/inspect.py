"""Deterministic driver repository impact inspection."""

from __future__ import annotations

import fnmatch
import re
import tomllib
from pathlib import Path, PurePosixPath

from .git import (
    GitError,
    check_worktree_unchanged,
    collect_changes,
    has_conflicts,
    list_target_paths,
    read_revision_file,
    read_worktree_file,
    repository_root,
    resolve_commit,
    sha256,
    worktree_identity,
)
from .machine import validate_impact_document
from .markdown import extract_commands, index_markdown, markdown_warnings
from .profile import ImpactProfile


class InspectionError(ValueError):
    """Raised when a deterministic inspection cannot be completed."""


class StaleRepositoryError(InspectionError):
    """Raised when consumed worktree bytes change during inspection."""


_EXPLICIT_ID = re.compile(
    r"\b(?:[A-Z][A-Z0-9]*-\d+|M\d+|[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+(?:@\d+)?)\b"
)


def _matches(path: str, patterns: tuple[str, ...] | list[str]) -> bool:
    pure = PurePosixPath(path)
    return any(fnmatch.fnmatchcase(path, pattern) or pure.match(pattern) for pattern in patterns)


def _read_target(
    root: Path,
    target_commit: str | None,
    path: str,
    max_bytes: int,
    consumed: dict[str, str],
) -> bytes | None:
    try:
        data = (
            read_revision_file(root, target_commit, path, max_bytes)
            if target_commit is not None
            else read_worktree_file(root, path, max_bytes)
        )
    except GitError as error:
        raise InspectionError(str(error)) from error
    if data is not None and len(data) > max_bytes:
        raise InspectionError(f"file exceeds max_file_bytes ({max_bytes}): {path}")
    if target_commit is None:
        digest = sha256(data) if data is not None else "<missing>"
        previous = consumed.get(path)
        if previous is not None and previous != digest:
            raise StaleRepositoryError(f"repository changed during inspection: {path}")
        consumed[path] = digest
    return data


def _packages(
    root: Path,
    target_commit: str | None,
    target_paths: list[str],
    changed_paths: set[str],
    max_bytes: int,
    consumed: dict[str, str],
) -> list[dict[str, str]]:
    manifests = [
        path for path in target_paths if path == "Cargo.toml" or path.endswith("/Cargo.toml")
    ]
    output: list[dict[str, str]] = []
    for manifest in manifests:
        data = _read_target(root, target_commit, manifest, max_bytes, consumed)
        if data is None:
            continue
        try:
            parsed = tomllib.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, tomllib.TOMLDecodeError):
            continue
        package = parsed.get("package")
        if not isinstance(package, dict) or not isinstance(package.get("name"), str):
            continue
        directory = PurePosixPath(manifest).parent.as_posix()
        directory = "" if directory == "." else directory
        prefix = f"{directory}/" if directory else ""
        if any(path == manifest or path.startswith(prefix) for path in changed_paths):
            output.append({"name": package["name"], "manifest": manifest})
    return sorted(output, key=lambda item: (item["manifest"], item["name"]))


def inspect_repository(
    repository: str | Path,
    profile: ImpactProfile,
    *,
    base: str = "HEAD",
    target: str = "worktree",
    excluded_paths: set[str] | None = None,
) -> dict[str, object]:
    """Inspect a local revision-to-revision or revision-to-worktree change."""

    try:
        root = repository_root(repository)
        if has_conflicts(root):
            raise InspectionError("repository has unresolved merge conflicts")
        base_commit = resolve_commit(root, base)
        target_commit = None if target == "worktree" else resolve_commit(root, target)
        changes, consumed = collect_changes(
            root,
            base_commit,
            target_commit,
            max_files=profile.limits["max_files"],
            max_diff_bytes=profile.limits["max_diff_bytes"],
            max_file_bytes=profile.limits["max_file_bytes"],
            excluded_paths=excluded_paths or set(),
        )
    except GitError as error:
        raise InspectionError(str(error)) from error

    ignored_changes: list[str] = []
    included_changes: list[dict[str, object]] = []
    for change in changes:
        if _matches(str(change["path"]), profile.ignored):
            ignored_changes.append(str(change["path"]))
        else:
            included_changes.append(change)
    changes = included_changes
    for index, change in enumerate(changes, 1):
        change["id"] = f"C-{index:03d}"
        matching_rules = [
            rule for rule in profile.rules if _matches(str(change["path"]), rule["globs"])
        ]
        change["rule_ids"] = [rule["id"] for rule in matching_rules]
        change["domains"] = sorted(
            {domain for rule in matching_rules for domain in rule["domains"]}
        )

    target_paths = list_target_paths(root, target_commit)
    authority: list[dict[str, object]] = []
    warnings: list[str] = []
    role_to_ids: dict[str, list[str]] = {}
    suggested_commands: list[str] = []
    for document in profile.documents:
        path = document["path"]
        data = _read_target(
            root,
            target_commit,
            path,
            profile.limits["max_file_bytes"],
            consumed,
        )
        if data is None:
            if document["required"]:
                raise InspectionError(f"required authority document is missing: {path}")
            warnings.append(f"optional authority document is missing: {path}")
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            warnings.append(f"authority document is not UTF-8 and was not indexed: {path}")
            continue
        entries = index_markdown(path, text, profile.limits["max_authority_text"])
        warnings.extend(markdown_warnings(path, text))
        if document.get("stable_ids", False) and not _EXPLICIT_ID.search(text):
            warnings.append(
                f"authority document has no explicit stable semantic IDs; structural hashes are used: {path}"
            )
        if len(authority) + len(entries) > profile.limits["max_authority_entries"]:
            raise InspectionError("authority index exceeds max_authority_entries")
        for entry in entries:
            entry["id"] = f"A-{len(authority) + 1:04d}"
            entry["role"] = document["role"]
            authority.append(entry)
            role_to_ids.setdefault(document["role"], []).append(str(entry["id"]))
        if document["role"] == "repository_policy":
            suggested_commands.extend(extract_commands(text))

    obligations: list[dict[str, object]] = []
    obligation_keys: dict[tuple[object, ...], dict[str, object]] = {}
    for change in changes:
        for rule in profile.rules:
            if rule["id"] not in change["rule_ids"]:
                continue
            for raw in rule["obligations"]:
                key = (rule["id"], raw["kind"], raw["strength"], raw["reason"])
                obligation = obligation_keys.get(key)
                if obligation is None:
                    obligation = {
                        "id": f"O-{len(obligations) + 1:03d}",
                        "kind": raw["kind"],
                        "strength": raw["strength"],
                        "reason": raw["reason"],
                        "rule_id": rule["id"],
                        "change_refs": [],
                        "authority_refs": sorted(
                            {
                                identifier
                                for role in raw["authority_roles"]
                                for identifier in role_to_ids.get(role, [])
                            }
                        ),
                        "checks": list(raw["checks"]),
                    }
                    obligation_keys[key] = obligation
                    obligations.append(obligation)
                obligation["change_refs"].append(change["id"])

    unclassified = [change["id"] for change in changes if not change["rule_ids"]]
    if unclassified:
        warnings.append("one or more changed paths were not classified by the selected profile")
    if any(change["patch_truncated"] for change in changes):
        warnings.append("one or more diff patches were truncated at the configured aggregate limit")
    if any(change["binary"] for change in changes):
        warnings.append("binary changes are identified by path and digest but have no text patch")

    changed_paths = {str(change["path"]) for change in changes}
    packages = _packages(
        root,
        target_commit,
        target_paths,
        changed_paths,
        profile.limits["max_file_bytes"],
        consumed,
    )
    try:
        if target_commit is None:
            check_worktree_unchanged(root, consumed, profile.limits["max_file_bytes"])
    except GitError as error:
        raise StaleRepositoryError(str(error)) from error

    domains = sorted({domain for change in changes for domain in change["domains"]})
    status = "review_required" if changes else "clear"
    snapshot_target = (
        {"kind": "worktree", "sha256": worktree_identity(consumed)}
        if target_commit is None
        else {"kind": "commit", "commit": target_commit}
    )
    return validate_impact_document(
        {
            "schema_version": 1,
            "task": "driver_change_impact",
            "snapshot": {
                "repository": str(root),
                "base": {"requested": base, "commit": base_commit},
                "target": snapshot_target,
            },
            "profile": {"name": profile.name, "schema_version": 1, "sha256": profile.sha256},
            "packages": packages,
            "changes": changes,
            "domains": domains,
            "authority_index": authority,
            "obligations": obligations,
            "unclassified": unclassified,
            "ignored_paths": sorted(ignored_changes),
            "suggested_commands": list(dict.fromkeys(suggested_commands)),
            "warnings": warnings,
            "result": {
                "status": status,
                "meaning": (
                    "no profile obligation was found; correctness was not evaluated"
                    if status == "clear"
                    else "changed surfaces require review; acceptability was not evaluated"
                ),
            },
        }
    )
