"""Deterministic changelog validation."""

from __future__ import annotations

import re
from datetime import date

from .model import Issue, normalize_entry_key, parse_bullet_entries
from .parser import ParseError, find_unfenced_matches, parse_changelog, split_unreleased
from .profile import Profile, semver_triplet, version_at_least

_TOP_TITLE = re.compile(r"^# Changelog\s*$", re.MULTILINE)
_LEVEL2 = re.compile(r"^## ", re.MULTILINE)
_LEVEL3 = re.compile(r"^### ", re.MULTILINE)


def _strict_release(version: str | None, profile: Profile) -> bool:
    if version is None:
        return True
    if version == "__INVALID__":
        return True
    return version_at_least(version, profile.strict_from_version)


def validate_text(text: str, profile: Profile, base_text: str | None = None) -> list[Issue]:
    issues: list[Issue] = []

    titles = find_unfenced_matches(text, _TOP_TITLE)
    level2_headings = find_unfenced_matches(text, _LEVEL2)
    first_l2 = level2_headings[0] if level2_headings else None
    if len(titles) != 1:
        issues.append(
            Issue("title.count", f"expected exactly one '# Changelog', found {len(titles)}")
        )
    elif first_l2 and titles[0].start() > first_l2.start():
        issues.append(Issue("title.order", "'# Changelog' must precede release headings"))

    try:
        changelog = parse_changelog(text)
    except ParseError as exc:
        return issues + [Issue("parse", str(exc))]

    unreleased = [r for r in changelog.releases if r.is_unreleased]
    if len(unreleased) != 1:
        issues.append(
            Issue(
                "unreleased.count",
                f"expected exactly one Unreleased section, found {len(unreleased)}",
            )
        )
    elif changelog.releases[0] is not unreleased[0]:
        issues.append(
            Issue(
                "unreleased.order",
                "Unreleased must be the first level-2 release section",
                unreleased[0].line,
            )
        )

    versions_seen: set[str] = set()
    previous_version: tuple[int, int, int] | None = None
    previous_date: date | None = None

    for release in changelog.releases:
        strict = _strict_release(release.version, profile)

        if not release.is_unreleased:
            if release.version == "__INVALID__" or release.date is None:
                issues.append(
                    Issue(
                        "release.heading",
                        "release heading must be '## X.Y.Z - YYYY-MM-DD' or '## [X.Y.Z] - YYYY-MM-DD'",
                        release.line,
                    )
                )
            else:
                try:
                    version_tuple = semver_triplet(release.version)
                except ValueError as exc:
                    issues.append(Issue("release.semver", str(exc), release.line))
                else:
                    if release.version in versions_seen:
                        issues.append(
                            Issue(
                                "release.duplicate",
                                f"duplicate release {release.version}",
                                release.line,
                            )
                        )
                    versions_seen.add(release.version)
                    if previous_version is not None and version_tuple >= previous_version:
                        issues.append(
                            Issue(
                                "release.order",
                                f"release {release.version} is not below previous release in descending SemVer order",
                                release.line,
                            )
                        )
                    previous_version = version_tuple

                try:
                    parsed_date = date.fromisoformat(release.date)
                except ValueError:
                    issues.append(
                        Issue(
                            "release.date", f"invalid ISO release date {release.date}", release.line
                        )
                    )
                else:
                    if previous_date is not None and parsed_date > previous_date:
                        issues.append(
                            Issue(
                                "release.date_order",
                                f"release date {release.date} is newer than the release above it",
                                release.line,
                            )
                        )
                    previous_date = parsed_date

        if not strict:
            continue

        if (
            not release.is_unreleased
            and profile.require_release_summary
            and profile.release_summary_prefix
            and not release.intro.lstrip().startswith(profile.release_summary_prefix)
        ):
            issues.append(
                Issue(
                    "release.summary",
                    f"release must begin with summary prefix {profile.release_summary_prefix!r}",
                    release.line + 1,
                )
            )

        names = [s.name for s in release.sections]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        for name in duplicates:
            first = next(s for s in release.sections if s.name == name)
            issues.append(Issue("section.duplicate", f"duplicate subsection '{name}'", first.line))

        order_map = {name: i for i, name in enumerate(profile.allowed_sections)}
        last_index = -1
        for section in release.sections:
            if section.name not in order_map:
                issues.append(
                    Issue(
                        "section.unknown",
                        f"unknown subsection '{section.name}'; allowed: {', '.join(profile.allowed_sections)}",
                        section.line,
                    )
                )
                continue
            idx = order_map[section.name]
            if idx < last_index:
                issues.append(
                    Issue(
                        "section.order",
                        f"subsection '{section.name}' is out of canonical order",
                        section.line,
                    )
                )
            last_index = max(last_index, idx)

            if not section.body.strip():
                issues.append(
                    Issue("section.empty", f"subsection '{section.name}' is empty", section.line)
                )
                continue

            if profile.section_entries_must_be_bullets:
                entries, stray = parse_bullet_entries(section.body)
                if stray:
                    issues.append(
                        Issue(
                            "section.missing_heading_or_bullet",
                            f"non-bullet content appears directly in subsection '{section.name}': {stray[0]!r}",
                            section.line + 1,
                        )
                    )
                if not entries:
                    issues.append(
                        Issue(
                            "section.no_entries",
                            f"subsection '{section.name}' contains no bullet entries",
                            section.line,
                        )
                    )
                else:
                    seen_entries: set[str] = set()
                    for entry in entries:
                        key = normalize_entry_key(entry)
                        if key in seen_entries:
                            issues.append(
                                Issue(
                                    "entry.duplicate",
                                    f"subsection '{section.name}' contains a duplicate entry",
                                    section.line + 1,
                                )
                            )
                        seen_entries.add(key)

        required = (
            profile.required_unreleased_sections
            if release.is_unreleased
            else profile.required_release_sections
        )
        for name in required:
            if name not in names:
                issues.append(
                    Issue(
                        "section.missing", f"required subsection '{name}' is missing", release.line
                    )
                )

        if release.is_unreleased:
            if release.intro.strip():
                bullet_line = next(
                    (ln for ln in release.intro.splitlines() if ln.startswith("- ")), None
                )
                if bullet_line:
                    issues.append(
                        Issue(
                            "unreleased.missing_section",
                            "Unreleased contains a bullet before any subsection; a section heading is missing",
                            release.line + 1,
                        )
                    )
            if not profile.allow_empty_unreleased and not release.sections:
                issues.append(
                    Issue(
                        "unreleased.empty",
                        "Unreleased must contain at least one subsection",
                        release.line,
                    )
                )

    # Detect level-3 headings before the first level-2 release heading, usually a malformed structure.
    if first_l2:
        pre_release = text[: first_l2.start()]
        if find_unfenced_matches(pre_release, _LEVEL3):
            issues.append(
                Issue(
                    "section.before_release",
                    "level-3 subsection appears before any release heading",
                )
            )

    if base_text is not None and profile.protect_released_history:
        try:
            current = split_unreleased(text)
            base = split_unreleased(base_text)
        except ParseError as exc:
            issues.append(Issue("history.compare", f"cannot compare released history: {exc}"))
        else:
            if current.released_history != base.released_history:
                issues.append(
                    Issue(
                        "history.modified",
                        "released changelog history differs from base; ordinary PRs may modify only Unreleased",
                    )
                )

    return issues
