"""Parser and protected-history slicing for supported changelog Markdown."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .model import Changelog, Release, Section

_RELEASE_HEADING = re.compile(r"^## (?P<label>[^\n]+)$", re.MULTILINE)
_SECTION_HEADING = re.compile(r"^### (?P<name>[^\n]+)$", re.MULTILINE)
_VERSION = r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?"
_VERSION_HEADING = re.compile(
    rf"^(?:\[(?P<bracketed>{_VERSION})\]|(?P<plain>{_VERSION})) - "
    r"(?P<date>\d{4}-\d{2}-\d{2})$"
)
_FENCE_OPEN = re.compile(r"^ {0,3}(?P<marker>`{3,}|~{3,})(?P<info>.*)$")
_HTML_COMMENT_OPEN = re.compile(r"^ {0,3}<!--")


class ParseError(ValueError):
    pass


def find_unfenced_matches(text: str, pattern: re.Pattern[str]) -> list[re.Match[str]]:
    """Find line-oriented Markdown matches outside backtick and tilde fences."""

    matches: list[re.Match[str]] = []
    fence_character: str | None = None
    fence_length = 0
    in_html_comment = False
    offset = 0

    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        if fence_character is not None:
            closing = re.fullmatch(
                rf" {{0,3}}{re.escape(fence_character)}{{{fence_length},}}[ \t]*",
                content,
            )
            if closing is not None:
                fence_character = None
                fence_length = 0
        elif in_html_comment:
            if "-->" in content:
                in_html_comment = False
        else:
            fence = _FENCE_OPEN.match(content)
            is_valid_fence = fence is not None and not (
                fence.group("marker").startswith("`") and "`" in fence.group("info")
            )
            if is_valid_fence:
                assert fence is not None
                marker = fence.group("marker")
                fence_character = marker[0]
                fence_length = len(marker)
            elif (comment := _HTML_COMMENT_OPEN.match(content)) is not None:
                in_html_comment = "-->" not in content[comment.end() :]
            else:
                match = pattern.match(text, offset)
                if match is not None:
                    matches.append(match)
        offset += len(line)

    return matches


def _is_unreleased_label(label: str) -> bool:
    return label.strip() in {"Unreleased", "[Unreleased]"}


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def parse_changelog(text: str) -> Changelog:
    matches = find_unfenced_matches(text, _RELEASE_HEADING)
    if not matches:
        raise ParseError("no level-2 release headings found")

    preamble = text[: matches[0].start()]
    releases: list[Release] = []

    for i, match in enumerate(matches):
        body_start = match.end()
        if body_start < len(text) and text[body_start] == "\n":
            body_start += 1
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end]
        raw_label = match.group("label").strip()
        line = _line_number(text, match.start())

        if _is_unreleased_label(raw_label):
            label = "Unreleased"
            version = None
            date = None
        else:
            label = raw_label
            vm = _VERSION_HEADING.fullmatch(raw_label)
            if vm:
                version = vm.group("bracketed") or vm.group("plain")
                date = vm.group("date")
            else:
                version = "__INVALID__"
                date = None

        section_matches = find_unfenced_matches(body, _SECTION_HEADING)
        intro_end = section_matches[0].start() if section_matches else len(body)
        intro = body[:intro_end].strip("\r\n")
        sections: list[Section] = []

        for j, sm in enumerate(section_matches):
            section_body_start = sm.end()
            if section_body_start < len(body) and body[section_body_start] == "\n":
                section_body_start += 1
            section_body_end = (
                section_matches[j + 1].start() if j + 1 < len(section_matches) else len(body)
            )
            section_body = body[section_body_start:section_body_end].strip("\r\n")
            sections.append(
                Section(
                    name=sm.group("name").strip(),
                    body=section_body,
                    line=line + body[: sm.start()].count("\n") + 1,
                )
            )

        releases.append(
            Release(
                label=label,
                version=version,
                date=date,
                intro=intro,
                sections=sections,
                line=line,
            )
        )

    return Changelog(preamble=preamble, releases=releases, text=text)


@dataclass(slots=True)
class DocumentSlices:
    preamble_through_unreleased_heading: str
    unreleased_body: str
    released_history: str


def split_unreleased(text: str) -> DocumentSlices:
    """Split while preserving historical bytes exactly.

    The prefix includes `## Unreleased` and its terminating newline. The history
    begins at the next `## ...` heading, or is empty when no release exists yet.
    """
    matches = find_unfenced_matches(text, _RELEASE_HEADING)
    unreleased = [m for m in matches if _is_unreleased_label(m.group("label"))]
    if len(unreleased) != 1:
        raise ParseError(f"expected exactly one Unreleased heading, found {len(unreleased)}")
    u = unreleased[0]
    idx = matches.index(u)
    prefix_end = u.end()
    if prefix_end < len(text) and text[prefix_end] == "\n":
        prefix_end += 1
    history_start = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
    return DocumentSlices(
        preamble_through_unreleased_heading=text[:prefix_end],
        unreleased_body=text[prefix_end:history_start],
        released_history=text[history_start:],
    )


def parse_unreleased_body(text: str) -> Release:
    synthetic = "# Changelog\n\n## Unreleased\n" + text
    return parse_changelog(synthetic).unreleased
