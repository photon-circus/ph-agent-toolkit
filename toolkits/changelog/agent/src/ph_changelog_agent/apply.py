"""Contract-checked experimental application of agent-generated entries."""

from __future__ import annotations

import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ph_changelog.operations import add_entry
from ph_changelog.profile import Profile
from ph_changelog.validate import validate_text

from .contracts import validate_agent_output


class StaleChangelogError(RuntimeError):
    """Raised instead of overwriting a changelog changed after model dispatch."""


@dataclass(frozen=True, slots=True)
class ChangelogSnapshot:
    raw: bytes
    text: str


def read_changelog_snapshot(path: str | Path) -> ChangelogSnapshot:
    raw = Path(path).read_bytes()
    return ChangelogSnapshot(raw=raw, text=raw.decode("utf-8"))


def apply_agent_output(
    changelog_text: str,
    output: object,
    facts: object,
    profile: Profile,
) -> str:
    """Apply contract-checked prose through the current core operations."""

    validate_agent_output(output, facts, set(profile.allowed_sections))
    assert isinstance(output, dict)  # Established by validation.
    assert isinstance(facts, dict)
    if output["status"] != "ok":
        raise ValueError(f"agent requested supervisor: {output.get('reason', 'unspecified')}")

    updated = changelog_text
    breaking = bool(facts.get("change", {}).get("breaking", False))
    for entry in output["entries"]:
        updated = add_entry(
            updated,
            profile,
            entry["section"],
            entry["text"],
            breaking=breaking,
        )
    issues = validate_text(updated, profile)
    if issues:
        raise ValueError(
            "agent output produced invalid changelog:\n" + "\n".join(str(issue) for issue in issues)
        )
    return updated


def atomic_write_if_unchanged(
    path: str | Path,
    expected: bytes | ChangelogSnapshot,
    updated_text: str,
) -> None:
    """Atomically replace ``path`` only if it still has the snapshotted bytes.

    A second comparison immediately before ``os.replace`` narrows the race
    between validation and replacement. The temporary file lives beside the
    target, so the final replacement stays on one filesystem.
    """

    target = Path(path)
    expected_raw = expected.raw if isinstance(expected, ChangelogSnapshot) else expected
    if target.read_bytes() != expected_raw:
        raise StaleChangelogError(f"{target} changed while the changelog agent was running")

    mode = stat.S_IMODE(target.stat().st_mode)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "wb") as stream:
            stream.write(updated_text.encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        if target.read_bytes() != expected_raw:
            raise StaleChangelogError(f"{target} changed while the changelog agent was running")
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()
