"""Experimental exact-snapshot machine representation for a changelog."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from .model import Issue, Release, parse_bullet_entries
from .parser import ParseError, parse_changelog
from .profile import Profile
from .validate import validate_text

MACHINE_FORMAT = "ph-changelog-document"
MACHINE_SCHEMA_VERSION = 1
UTF8_BOM = b"\xef\xbb\xbf"

_SOURCE_FIELDS = {
    "file": {"kind", "path"},
    "stdin": {"kind"},
    "http": {
        "kind",
        "requested_url",
        "final_url",
        "query_redacted",
        "status",
        "content_type",
        "etag",
        "last_modified",
    },
}


def _closed_source(source: Mapping[str, object]) -> dict[str, object]:
    kind = source.get("kind")
    if not isinstance(kind, str) or kind not in _SOURCE_FIELDS:
        raise ValueError("machine source kind must be 'file', 'stdin', or 'http'")
    expected = _SOURCE_FIELDS[kind]
    actual = set(source)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        details: list[str] = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if extra:
            details.append("unexpected: " + ", ".join(extra))
        raise ValueError(f"invalid {kind} machine source ({'; '.join(details)})")

    if kind == "file":
        if not isinstance(source["path"], str) or not source["path"]:
            raise ValueError("file machine source path must be a non-empty string")
    elif kind == "http":
        for field in ("requested_url", "final_url"):
            if not isinstance(source[field], str) or not source[field]:
                raise ValueError(f"HTTP machine source {field} must be a non-empty string")
        if not isinstance(source["query_redacted"], bool):
            raise ValueError("HTTP machine source query_redacted must be a boolean")
        status = source["status"]
        if not isinstance(status, int) or isinstance(status, bool) or status != 200:
            raise ValueError("HTTP machine source status must be the integer 200")
        for field in ("content_type", "etag", "last_modified"):
            if source[field] is not None and not isinstance(source[field], str):
                raise ValueError(f"HTTP machine source {field} must be a string or null")
    return dict(source)


def _entry_text(markdown: str) -> str:
    lines = markdown.splitlines()
    if not lines:
        return ""
    first = lines[0][2:] if lines[0].startswith("- ") else lines[0]
    continuation = [line[2:] if line.startswith("  ") else line for line in lines[1:]]
    return "\n".join([first, *continuation]).rstrip()


def _release_kind(release: Release) -> str:
    if release.is_unreleased:
        return "unreleased"
    if release.version == "__INVALID__":
        return "invalid"
    return "release"


def _release_document(release: Release) -> dict[str, Any]:
    sections: list[dict[str, Any]] = []
    for section in release.sections:
        entries, unparsed_lines = parse_bullet_entries(section.body)
        sections.append(
            {
                "name": section.name,
                "line": section.line,
                "body": section.body,
                "entries": [{"markdown": entry, "text": _entry_text(entry)} for entry in entries],
                "unparsed_lines": unparsed_lines,
            }
        )

    return {
        "kind": _release_kind(release),
        "label": release.label,
        "version": None if release.version == "__INVALID__" else release.version,
        "date": release.date,
        "line": release.line,
        "intro": release.intro,
        "sections": sections,
    }


def _issue_document(issue: Issue) -> dict[str, object]:
    return {
        "code": issue.code,
        "message": issue.message,
        "line": issue.line,
        "severity": issue.severity,
    }


def deconstruct_changelog(
    raw: bytes,
    profile: Profile,
    source: Mapping[str, object],
) -> dict[str, Any]:
    """Decode and deconstruct one exact UTF-8 changelog snapshot.

    ``artifact.raw_text`` is the lossless representation. Semantic parsing
    ignores a leading UTF-8 BOM while retaining it in the artifact and digest.
    """

    if not isinstance(raw, bytes):
        raise TypeError("raw changelog must be bytes")
    raw_text = raw.decode("utf-8")
    semantic_text = raw_text.removeprefix("\ufeff")
    issues = validate_text(semantic_text, profile)
    try:
        parsed = parse_changelog(semantic_text)
    except ParseError:
        document = None
    else:
        document = {
            "preamble": parsed.preamble,
            "releases": [_release_document(release) for release in parsed.releases],
        }

    return {
        "format": MACHINE_FORMAT,
        "schema_version": MACHINE_SCHEMA_VERSION,
        "source": _closed_source(source),
        "artifact": {
            "encoding": "utf-8",
            "utf8_bom": raw.startswith(UTF8_BOM),
            "byte_length": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "raw_text": raw_text,
        },
        "document": document,
        "validation": {
            "profile": profile.name,
            "valid": not issues,
            "issues": [_issue_document(issue) for issue in issues],
        },
    }


def render_machine_json(document: Mapping[str, object]) -> str:
    """Render deterministic UTF-8-ready JSON for a machine document."""

    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"
