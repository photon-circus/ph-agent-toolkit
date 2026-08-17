"""Changelog normalization and structured insertion experiments."""

from __future__ import annotations

from dataclasses import replace

from .model import (
    Release,
    Section,
    format_entry,
    normalize_entry_key,
    parse_bullet_entries,
    unique_entries,
)
from .parser import parse_unreleased_body, split_unreleased
from .profile import Profile


def _normalize_newlines(text: str) -> str:
    """Normalize parsed content before rendering in the document's newline style."""

    return text.replace("\r\n", "\n").replace("\r", "\n")


def _canonical_sections(release: Release, profile: Profile) -> list[Section]:
    order = {name: i for i, name in enumerate(profile.allowed_sections)}
    # Unknown sections are deliberately retained at the end. The validator will
    # reject them; normalize must not silently delete content.
    return sorted(release.sections, key=lambda s: order.get(s.name, len(order)))


def render_unreleased_body(
    release: Release,
    profile: Profile,
    newline: str = "\n",
) -> str:
    chunks: list[str] = []
    intro = _normalize_newlines(release.intro).strip("\n")
    if intro:
        chunks.append(intro.rstrip())

    for section in _canonical_sections(release, profile):
        body = _normalize_newlines(section.body).strip("\n").rstrip()
        if not body:
            continue
        chunks.append(f"### {section.name}\n{body}")

    if not chunks:
        rendered = "\n"
    else:
        rendered = "\n\n" + "\n\n".join(chunks) + "\n\n"
    return rendered if newline == "\n" else rendered.replace("\n", newline)


def _document_newline(prefix: str) -> str:
    return "\r\n" if prefix.endswith("\r\n") else "\n"


def _coalesce_duplicate_sections(release: Release) -> Release:
    by_name: dict[str, list[str]] = {}
    order: list[str] = []
    lines: dict[str, int] = {}
    for section in release.sections:
        entries, stray = parse_bullet_entries(section.body)
        if stray:
            raise ValueError(
                f"cannot normalize subsection '{section.name}': non-bullet content exists"
            )
        if section.name not in by_name:
            by_name[section.name] = []
            order.append(section.name)
            lines[section.name] = section.line
        by_name[section.name].extend(entries)

    sections = [
        Section(name=name, body="\n".join(unique_entries(by_name[name])), line=lines[name])
        for name in order
        if by_name[name]
    ]
    return replace(release, sections=sections)


def normalize_unreleased(text: str, profile: Profile) -> str:
    slices = split_unreleased(text)
    release = _coalesce_duplicate_sections(parse_unreleased_body(slices.unreleased_body))
    return (
        slices.preamble_through_unreleased_heading.rstrip("\r\n")
        + render_unreleased_body(
            release,
            profile,
            _document_newline(slices.preamble_through_unreleased_heading),
        )
        + slices.released_history.lstrip("\r\n")
    )


def add_entry(
    text: str, profile: Profile, section_name: str, entry_text: str, breaking: bool = False
) -> str:
    if section_name not in profile.allowed_sections:
        raise ValueError(f"section '{section_name}' is not allowed")

    slices = split_unreleased(text)
    release = parse_unreleased_body(slices.unreleased_body)

    formatted = format_entry(entry_text)
    if breaking:
        marker = profile.breaking_prefix
        first = formatted[2:]
        if not first.startswith(marker):
            formatted = f"- {marker} {first}"

    existing = release.section(section_name)
    if existing is None:
        release.sections.append(Section(name=section_name, body=formatted, line=0))
    else:
        entries, stray = parse_bullet_entries(existing.body)
        if stray:
            raise ValueError(
                f"cannot add to malformed section '{section_name}': stray content exists"
            )
        key = normalize_entry_key(formatted)
        if key not in {normalize_entry_key(e) for e in entries}:
            body = "\n".join(unique_entries([*entries, formatted]))
            for idx, section in enumerate(release.sections):
                if section is existing:
                    release.sections[idx] = replace(existing, body=body)
                    break

    return (
        slices.preamble_through_unreleased_heading.rstrip("\r\n")
        + render_unreleased_body(
            release,
            profile,
            _document_newline(slices.preamble_through_unreleased_heading),
        )
        + slices.released_history.lstrip("\r\n")
    )
