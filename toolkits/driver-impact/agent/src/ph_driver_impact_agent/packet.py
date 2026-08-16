"""Bounded deterministic projection of an impact document for a local model."""

from __future__ import annotations

import json
import re
from typing import Any

from ph_driver_impact.machine import validate_impact_document

MAX_PATCH_CHARS = 12_000
MAX_TOTAL_PATCH_CHARS = 64_000
MAX_AUTHORITY = 160
MAX_PACKET_BYTES = 160_000
_TOKEN = re.compile(r"[a-z][a-z0-9_]{2,}")


def _terms(document: dict[str, Any]) -> set[str]:
    text = " ".join(
        [*document["domains"]]
        + [str(change["path"]) for change in document["changes"]]
        + [check for obligation in document["obligations"] for check in obligation["checks"]]
    ).lower()
    stop = {"the", "and", "for", "with", "from", "changed", "review", "driver"}
    return {token for token in _TOKEN.findall(text) if token not in stop}


def build_task_packet(impact: object) -> dict[str, Any]:
    document = validate_impact_document(impact)
    patches = 0
    changes: list[dict[str, Any]] = []
    for item in document["changes"]:
        remaining = max(MAX_TOTAL_PATCH_CHARS - patches, 0)
        patch = item["patch"][: min(MAX_PATCH_CHARS, remaining)]
        patches += len(patch)
        changes.append(
            {
                "id": item["id"],
                "path": item["path"],
                "old_path": item["old_path"],
                "status": item["status"],
                "binary": item["binary"],
                "rule_ids": item["rule_ids"],
                "domains": item["domains"],
                "patch": patch,
                "patch_omitted": len(patch) < len(item["patch"]) or item["patch_truncated"],
            }
        )

    eligible = {ref for item in document["obligations"] for ref in item["authority_refs"]}
    terms = _terms(document)

    def score(item: dict[str, Any]) -> tuple[int, str]:
        searchable = (item["text"] + " " + " ".join(item["heading_path"])).lower()
        value = (4 if item["kind"] == "heading" else 0) + sum(
            1 for term in terms if term in searchable
        )
        return (-value, item["id"])

    candidates = [item for item in document["authority_index"] if item["id"] in eligible]
    authority = sorted(candidates, key=score)[:MAX_AUTHORITY]
    packet = {
        "schema_version": 1,
        "task": "map_driver_change_impact",
        "source_snapshot": document["snapshot"],
        "profile": document["profile"],
        "packages": document["packages"],
        "changes": changes,
        "domains": document["domains"],
        "authority": authority,
        "authority_omitted": len(candidates) - len(authority),
        "obligations": document["obligations"],
        "unclassified": document["unclassified"],
        "warnings": document["warnings"],
        "constraints": {
            "read_only": True,
            "checks_executed": False,
            "capability_promotion_allowed": False,
            "invented_references_allowed": False,
        },
    }
    encoded = json.dumps(packet, ensure_ascii=False).encode("utf-8")
    if len(encoded) > MAX_PACKET_BYTES:
        raise ValueError(f"semantic task packet exceeds {MAX_PACKET_BYTES} bytes")
    return packet
