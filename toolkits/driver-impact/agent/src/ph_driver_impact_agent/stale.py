"""Revalidate a core worktree snapshot before and after a model call."""

from __future__ import annotations

from pathlib import Path

from ph_driver_impact import inspect_repository, load_profile
from ph_driver_impact.git import relative_output, repository_root
from ph_driver_impact.machine import validate_impact_document


class StaleImpactError(ValueError):
    """Raised when a saved impact document no longer describes the repository."""


def verify_current(
    impact: object,
    impact_path: str | Path | None = None,
    profile_path: str | Path | None = None,
) -> None:
    document = validate_impact_document(impact)
    snapshot = document["snapshot"]
    target = snapshot["target"]
    if target["kind"] == "commit":
        # Immutable local Git object identity is enough; inspect_repository will
        # also refuse if either object is no longer available.
        target_name = target["commit"]
    else:
        target_name = "worktree"
    root = repository_root(snapshot["repository"])
    excluded: set[str] = set()
    if impact_path is not None:
        relative = relative_output(root, str(impact_path))
        if relative:
            excluded.add(relative)
    profile = load_profile(
        str(profile_path) if profile_path is not None else document["profile"]["name"]
    )
    if profile.sha256 != document["profile"]["sha256"]:
        raise StaleImpactError("selected profile no longer matches the impact document")
    current = inspect_repository(
        root,
        profile,
        base=snapshot["base"]["commit"],
        target=target_name,
        excluded_paths=excluded,
    )
    if current["snapshot"]["target"] != target:
        raise StaleImpactError("repository target no longer matches the impact document")
