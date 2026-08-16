"""Stable machine and human rendering."""

from __future__ import annotations

import json


def render_json(document: dict[str, object]) -> str:
    return json.dumps(document, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def render_summary(document: dict[str, object]) -> str:
    result = document["result"]
    lines = [f"Impact: {str(result['status']).replace('_', ' ')}", ""]
    changes = document["changes"]
    lines.append(f"Changed files: {len(changes)}")
    packages = document["packages"]
    if packages:
        lines.append("Packages: " + ", ".join(item["name"] for item in packages))
    domains = document["domains"]
    if domains:
        lines.append("Domains: " + ", ".join(domains))
    obligations = document["obligations"]
    if obligations:
        lines.extend(["", "Obligations:"])
        for obligation in obligations:
            lines.append(
                f"  [{obligation['strength']}] {obligation['kind']}: {obligation['reason']}"
            )
    if document["unclassified"]:
        lines.extend(["", "Unclassified changes: " + ", ".join(document["unclassified"])])
    if document["warnings"]:
        lines.extend(["", "Warnings:"])
        lines.extend(f"  - {warning}" for warning in document["warnings"])
    lines.extend(["", "No implementation correctness or check result is implied.", ""])
    return "\n".join(lines)
