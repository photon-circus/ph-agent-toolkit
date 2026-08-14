"""Structured changelog document model and entry helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field


@dataclass(slots=True)
class Section:
    name: str
    body: str
    line: int


@dataclass(slots=True)
class Release:
    label: str
    version: str | None
    date: str | None
    intro: str
    sections: list[Section] = field(default_factory=list)
    line: int = 0

    @property
    def is_unreleased(self) -> bool:
        return self.version is None and self.label == "Unreleased"

    def section(self, name: str) -> Section | None:
        for section in self.sections:
            if section.name == name:
                return section
        return None


@dataclass(slots=True)
class Changelog:
    preamble: str
    releases: list[Release]
    text: str

    @property
    def unreleased(self) -> Release:
        for release in self.releases:
            if release.is_unreleased:
                return release
        raise ValueError("CHANGELOG has no Unreleased section")


@dataclass(slots=True)
class Issue:
    code: str
    message: str
    line: int | None = None
    severity: str = "error"

    def __str__(self) -> str:
        where = f"line {self.line}: " if self.line else ""
        return f"{self.severity.upper()} {self.code}: {where}{self.message}"


def normalize_entry_key(text: str) -> str:
    """Normalize an entry for duplicate detection without rewriting public prose."""
    text = text.strip()
    if text.startswith("- "):
        text = text[2:]
    return " ".join(text.split())


def parse_bullet_entries(body: str) -> tuple[list[str], list[str]]:
    """Return bullet blocks and stray non-bullet lines outside any entry.

    Wrapped continuation lines belong to the preceding bullet. Blank lines are
    tolerated between entries. A non-blank line before the first bullet is
    returned as stray content and can be rejected by policy.
    """
    entries: list[str] = []
    stray: list[str] = []
    current: list[str] | None = None

    for line in body.splitlines():
        if line.startswith("- "):
            if current is not None:
                entries.append("\n".join(current).rstrip())
            current = [line]
            continue

        if current is not None:
            if not line.strip():
                # Keep an internal blank only when prose resumes afterwards.
                current.append("")
            else:
                current.append(line)
            continue

        if line.strip():
            stray.append(line)

    if current is not None:
        entries.append("\n".join(current).rstrip())

    return entries, stray


def format_entry(text: str) -> str:
    """Serialize an LLM-produced entry as one Markdown bullet block."""
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("entry text is empty")
    if cleaned.startswith("- "):
        cleaned = cleaned[2:]
    lines = cleaned.splitlines()
    result = [f"- {lines[0].strip()}"]
    for line in lines[1:]:
        if line.strip():
            result.append(f"  {line.strip()}")
        else:
            result.append("")
    return "\n".join(result).rstrip()


def unique_entries(entries: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for entry in entries:
        key = normalize_entry_key(entry)
        if key not in seen:
            seen.add(key)
            out.append(entry)
    return out
