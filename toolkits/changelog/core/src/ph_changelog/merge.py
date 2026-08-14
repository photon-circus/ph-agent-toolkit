"""Conservative additive semantic merge for Unreleased entries."""

from __future__ import annotations

from .model import Release, Section, normalize_entry_key, parse_bullet_entries
from .operations import render_unreleased_body
from .parser import ParseError, parse_unreleased_body, split_unreleased
from .profile import Profile


class MergeConflict(RuntimeError):
    pass


def _entry_map(section: Section | None) -> tuple[list[str], dict[str, str]]:
    if section is None:
        return [], {}
    entries, stray = parse_bullet_entries(section.body)
    if stray:
        raise MergeConflict(
            f"section '{section.name}' has non-bullet content; refusing semantic merge"
        )
    by_key = {normalize_entry_key(entry): entry for entry in entries}
    if len(by_key) != len(entries):
        raise MergeConflict(
            f"section '{section.name}' contains duplicate entries; refusing semantic merge"
        )
    return entries, by_key


def _section_names(release: Release) -> set[str]:
    return {section.name for section in release.sections}


def _assert_unique_sections(release: Release, source_name: str) -> None:
    names = [section.name for section in release.sections]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise MergeConflict(
            f"{source_name} contains duplicate subsection(s): {', '.join(duplicates)}"
        )


def _merge_history(
    base: str,
    ours: str,
    theirs: str,
    *,
    protect: bool,
) -> str:
    if protect:
        if ours != base:
            raise MergeConflict("OURS modifies released history")
        if theirs != base:
            raise MergeConflict("THEIRS modifies released history")
        return base
    if ours == theirs:
        return ours
    if ours == base:
        return theirs
    if theirs == base:
        return ours
    raise MergeConflict("both branches modify released history differently")


def _assert_additive(base: Release, branch: Release, branch_name: str) -> None:
    if base.intro.strip() != branch.intro.strip():
        raise MergeConflict(
            f"{branch_name} modified Unreleased narrative text; only subsection entries auto-merge"
        )

    for base_section in base.sections:
        _, base_map = _entry_map(base_section)
        _, branch_map = _entry_map(branch.section(base_section.name))
        missing = [key for key in base_map if key not in branch_map]
        if missing:
            raise MergeConflict(
                f"{branch_name} removed or edited an existing '{base_section.name}' entry; only additive changes auto-merge"
            )


def merge_changelogs(base_text: str, ours_text: str, theirs_text: str, profile: Profile) -> str:
    try:
        base_s = split_unreleased(base_text)
        ours_s = split_unreleased(ours_text)
        theirs_s = split_unreleased(theirs_text)
    except ParseError as exc:
        raise MergeConflict(str(exc)) from exc

    if ours_s.preamble_through_unreleased_heading != base_s.preamble_through_unreleased_heading:
        raise MergeConflict("OURS modifies the changelog preamble or Unreleased heading")
    if theirs_s.preamble_through_unreleased_heading != base_s.preamble_through_unreleased_heading:
        raise MergeConflict("THEIRS modifies the changelog preamble or Unreleased heading")
    released_history = _merge_history(
        base_s.released_history,
        ours_s.released_history,
        theirs_s.released_history,
        protect=profile.protect_released_history,
    )

    base = parse_unreleased_body(base_s.unreleased_body)
    ours = parse_unreleased_body(ours_s.unreleased_body)
    theirs = parse_unreleased_body(theirs_s.unreleased_body)
    _assert_unique_sections(base, "BASE")
    _assert_unique_sections(ours, "OURS")
    _assert_unique_sections(theirs, "THEIRS")

    _assert_additive(base, ours, "OURS")
    _assert_additive(base, theirs, "THEIRS")

    all_names = _section_names(base) | _section_names(ours) | _section_names(theirs)
    unknown = sorted(all_names - set(profile.allowed_sections))
    if unknown:
        raise MergeConflict(f"unknown subsection(s): {', '.join(unknown)}")

    merged = Release(label="Unreleased", version=None, date=None, intro=base.intro, sections=[])

    for name in profile.allowed_sections:
        if name not in all_names:
            continue
        base_entries, _ = _entry_map(base.section(name))
        ours_entries, _ = _entry_map(ours.section(name))
        theirs_entries, _ = _entry_map(theirs.section(name))

        merged_entries = list(base_entries)
        keys = {normalize_entry_key(e) for e in merged_entries}

        for source_entries in (ours_entries, theirs_entries):
            for entry in source_entries:
                key = normalize_entry_key(entry)
                if key not in keys:
                    merged_entries.append(entry)
                    keys.add(key)

        if merged_entries:
            merged.sections.append(Section(name=name, body="\n".join(merged_entries), line=0))

    return (
        base_s.preamble_through_unreleased_heading.rstrip("\r\n")
        + render_unreleased_body(
            merged,
            profile,
            "\r\n" if base_s.preamble_through_unreleased_heading.endswith("\r\n") else "\n",
        )
        + released_history.lstrip("\r\n")
    )
