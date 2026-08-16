"""Small deterministic Markdown structural indexer."""

from __future__ import annotations

import hashlib
import re

_HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
_TABLE_SEPARATOR_CELL = re.compile(r"^:?-{3,}:?$")


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _is_table_row(line: str) -> bool:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return False
    cells = [cell.strip() for cell in stripped[1:-1].split("|")]
    return bool(cells) and not all(_TABLE_SEPARATOR_CELL.fullmatch(cell) for cell in cells)


def index_markdown(path: str, text: str, max_text: int) -> list[dict[str, object]]:
    """Index headings and non-separator table rows with content hashes."""

    entries: list[dict[str, object]] = []
    heading_stack: list[str] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        heading = _HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            heading_stack = heading_stack[: level - 1]
            heading_stack.append(title)
            normalized = " > ".join(heading_stack)
            entries.append(
                {
                    "path": path,
                    "kind": "heading",
                    "heading_path": list(heading_stack),
                    "text": title[:max_text],
                    "sha256": _digest(normalized),
                    "line": line_number,
                }
            )
        elif _is_table_row(line):
            normalized = " ".join(line.strip().split())
            entries.append(
                {
                    "path": path,
                    "kind": "table_row",
                    "heading_path": list(heading_stack),
                    "text": normalized[:max_text],
                    "sha256": _digest(" > ".join(heading_stack) + "\n" + normalized),
                    "line": line_number,
                }
            )
    return entries


def extract_commands(text: str) -> list[str]:
    """Extract non-comment lines from fenced blocks under a Commands heading."""

    commands: list[str] = []
    under_commands = False
    fence = False
    command_level = 0
    for line in text.splitlines():
        heading = _HEADING.match(line)
        if heading and not fence:
            level = len(heading.group(1))
            title = heading.group(2).strip().lower()
            if title == "commands":
                under_commands = True
                command_level = level
            elif under_commands and level <= command_level:
                under_commands = False
        if under_commands and line.strip().startswith("```"):
            fence = not fence
            continue
        if under_commands and fence:
            candidate = line.strip()
            if candidate and not candidate.startswith("#"):
                commands.append(candidate)
    return commands


def markdown_warnings(path: str, text: str) -> list[str]:
    """Return conservative warnings for visibly incomplete pipe-table rows."""

    warnings: list[str] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or "|" not in stripped:
            continue
        if stripped.startswith("|") != stripped.endswith("|"):
            warnings.append(f"malformed pipe-table row was not indexed: {path}:{line_number}")
    return warnings
