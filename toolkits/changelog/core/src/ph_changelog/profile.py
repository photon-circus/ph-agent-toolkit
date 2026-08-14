"""Changelog policy profiles and version helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import Any

_PROFILE_FIELDS = {
    "name",
    "allowed_sections",
    "strict_from_version",
    "required_unreleased_sections",
    "required_release_sections",
    "allow_empty_unreleased",
    "section_entries_must_be_bullets",
    "protect_released_history",
    "breaking_prefix",
    "release_summary_prefix",
    "require_release_summary",
}


def _string_list(data: dict[str, Any], field_name: str) -> list[str]:
    value = data.get(field_name, [])
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"profile {field_name} must be a string array")
    if len(set(value)) != len(value):
        raise ValueError(f"profile {field_name} must be unique")
    return list(value)


def _boolean(data: dict[str, Any], field_name: str, default: bool) -> bool:
    value = data.get(field_name, default)
    if not isinstance(value, bool):
        raise ValueError(f"profile {field_name} must be a boolean")
    return value


def _optional_string(data: dict[str, Any], field_name: str) -> str | None:
    value = data.get(field_name)
    if value is not None and not isinstance(value, str):
        raise ValueError(f"profile {field_name} must be a string or null")
    return value


@dataclass(slots=True)
class Profile:
    name: str
    allowed_sections: list[str]
    strict_from_version: str | None = None
    required_unreleased_sections: list[str] = field(default_factory=list)
    required_release_sections: list[str] = field(default_factory=list)
    allow_empty_unreleased: bool = True
    section_entries_must_be_bullets: bool = True
    protect_released_history: bool = True
    breaking_prefix: str = "**Breaking:**"
    release_summary_prefix: str | None = None
    require_release_summary: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Profile:
        extras = sorted(set(data) - _PROFILE_FIELDS)
        if extras:
            raise ValueError(f"profile has unexpected field(s): {', '.join(extras)}")
        if "allowed_sections" not in data:
            raise ValueError("profile is missing allowed_sections")
        allowed_sections = data["allowed_sections"]
        if (
            not isinstance(allowed_sections, list)
            or not allowed_sections
            or not all(isinstance(name, str) and name for name in allowed_sections)
        ):
            raise ValueError("profile allowed_sections must be a non-empty string array")
        if len(set(allowed_sections)) != len(allowed_sections):
            raise ValueError("profile allowed_sections must be unique")
        name = data.get("name", "default")
        if not isinstance(name, str) or not name:
            raise ValueError("profile name must be a non-empty string")
        strict_from_version = _optional_string(data, "strict_from_version")
        if strict_from_version is not None:
            semver_triplet(strict_from_version)
        breaking_prefix = data.get("breaking_prefix", "**Breaking:**")
        if not isinstance(breaking_prefix, str) or not breaking_prefix:
            raise ValueError("profile breaking_prefix must be a non-empty string")

        profile = cls(
            name=name,
            allowed_sections=list(allowed_sections),
            strict_from_version=strict_from_version,
            required_unreleased_sections=_string_list(data, "required_unreleased_sections"),
            required_release_sections=_string_list(data, "required_release_sections"),
            allow_empty_unreleased=_boolean(data, "allow_empty_unreleased", True),
            section_entries_must_be_bullets=_boolean(data, "section_entries_must_be_bullets", True),
            protect_released_history=_boolean(data, "protect_released_history", True),
            breaking_prefix=breaking_prefix,
            release_summary_prefix=_optional_string(data, "release_summary_prefix"),
            require_release_summary=_boolean(data, "require_release_summary", False),
        )
        unknown_required = (
            set(profile.required_unreleased_sections) | set(profile.required_release_sections)
        ) - set(profile.allowed_sections)
        if unknown_required:
            raise ValueError(
                "profile requires unknown section(s): " + ", ".join(sorted(unknown_required))
            )
        if profile.require_release_summary and not profile.release_summary_prefix:
            raise ValueError("profile require_release_summary needs release_summary_prefix")
        return profile


def load_profile(reference: str | Path) -> Profile:
    """Load a JSON file or a profile bundled with ``ph-changelog`` by name."""

    path = Path(reference)
    if path.is_file():
        data = json.loads(path.read_bytes().decode("utf-8"))
    else:
        name = str(reference)
        if name.endswith(".json"):
            name = name[:-5]
        resource = files("ph_changelog").joinpath("profiles", f"{name}.json")
        if not resource.is_file():
            raise FileNotFoundError(f"unknown changelog profile or file: {reference}")
        data = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("profile JSON must contain an object")
    return Profile.from_dict(data)


def semver_triplet(version: str) -> tuple[int, int, int]:
    core = version.split("+", 1)[0].split("-", 1)[0]
    parts = core.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f"not a simple SemVer version: {version}")
    return tuple(int(p) for p in parts)  # type: ignore[return-value]


def version_at_least(version: str, floor: str | None) -> bool:
    if floor is None:
        return True
    return semver_triplet(version) >= semver_triplet(floor)
