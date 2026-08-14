"""Command-line interface for deterministic changelog operations."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from .machine import deconstruct_changelog, render_machine_json
from .merge import MergeConflict, merge_changelogs
from .operations import add_entry, normalize_unreleased
from .profile import Profile, load_profile
from .validate import validate_text

DEFAULT_PROFILE = os.environ.get("PH_CHANGELOG_PROFILE", "photon-circus")
_ADD_ENTRY_KEYS = frozenset({"section", "entry", "breaking"})


def _read(path: str | Path) -> str:
    return Path(path).read_bytes().decode("utf-8")


def _write(path: str | Path, text: str) -> None:
    Path(path).write_bytes(text.encode("utf-8"))


def _write_atomic(path: str | Path, text: str) -> None:
    target = Path(path)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "wb") as stream:
            stream.write(text.encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_or_print(path: str, text: str, write: bool) -> None:
    if write:
        _write(path, text)
    else:
        sys.stdout.write(text)


def _write_stdout_utf8(text: str) -> None:
    stream = getattr(sys.stdout, "buffer", None)
    if stream is None:
        sys.stdout.write(text)
    else:
        stream.write(text.encode("utf-8"))


def _profile(args: argparse.Namespace) -> Profile:
    return load_profile(args.profile)


def _parse_add_operations(value: object) -> list[tuple[str, str, bool]]:
    if not isinstance(value, dict):
        raise ValueError("--input must contain a JSON object")

    if "entries" in value:
        unknown = set(value) - {"entries"}
        if unknown:
            raise ValueError("input object contains unknown fields: " + ", ".join(sorted(unknown)))
        entries = value["entries"]
        if not isinstance(entries, list) or not entries:
            raise ValueError("input entries must be a non-empty array")
    else:
        entries = [value]

    operations: list[tuple[str, str, bool]] = []
    for index, item in enumerate(entries):
        label = f"input entry {index + 1}"
        if not isinstance(item, dict):
            raise ValueError(f"{label} must be an object")

        unknown = set(item) - _ADD_ENTRY_KEYS
        if unknown:
            raise ValueError(f"{label} contains unknown fields: " + ", ".join(sorted(unknown)))
        missing = {"section", "entry"} - set(item)
        if missing:
            raise ValueError(f"{label} is missing required fields: " + ", ".join(sorted(missing)))

        section = item["section"]
        entry = item["entry"]
        breaking = item.get("breaking", False)
        if not isinstance(section, str) or not section.strip():
            raise ValueError(f"{label} section must be a non-empty string")
        if not isinstance(entry, str) or not entry.strip():
            raise ValueError(f"{label} entry must be a non-empty string")
        if type(breaking) is not bool:
            raise ValueError(f"{label} breaking must be a boolean")
        operations.append((section, entry, breaking))

    return operations


def cmd_check(args: argparse.Namespace) -> int:
    text = _read(args.path)
    base = _read(args.base) if args.base else None
    issues = validate_text(text, _profile(args), base_text=base)
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        return 1
    print(f"OK: {args.path}")
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    if args.path == "-":
        raw = sys.stdin.buffer.read()
        source: dict[str, object] = {"kind": "stdin"}
    else:
        raw = Path(args.path).read_bytes()
        source = {"kind": "file", "path": args.path}

    if args.output != "-" and args.path != "-":
        if Path(args.output).resolve() == Path(args.path).resolve():
            raise ValueError("--output must not overwrite the source changelog")

    machine_document = deconstruct_changelog(raw, _profile(args), source)
    rendered = render_machine_json(machine_document)
    if args.output == "-":
        _write_stdout_utf8(rendered)
    else:
        _write_atomic(args.output, rendered)
    return 0 if machine_document["validation"]["valid"] else 1


def cmd_normalize(args: argparse.Namespace) -> int:
    profile = _profile(args)
    text = normalize_unreleased(_read(args.path), profile)
    issues = validate_text(text, profile)
    if issues:
        raise ValueError("result failed validation:\n" + "\n".join(map(str, issues)))
    _write_or_print(args.path, text, args.write)
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    profile = _profile(args)
    text = _read(args.path)
    if args.input:
        operations = _parse_add_operations(json.loads(_read(args.input)))
        for section, entry, breaking in operations:
            text = add_entry(
                text,
                profile,
                section,
                entry,
                breaking=breaking,
            )
    else:
        if not args.section:
            raise ValueError("--section is required without --input")
        if args.entry_file:
            entry = _read(args.entry_file).strip()
        elif args.entry:
            entry = args.entry
        else:
            raise ValueError("--entry or --entry-file is required without --input")
        text = add_entry(text, profile, args.section, entry, breaking=args.breaking)

    issues = validate_text(text, profile)
    if issues:
        raise ValueError("result failed validation:\n" + "\n".join(map(str, issues)))
    _write_or_print(args.path, text, args.write)
    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    profile = _profile(args)
    base = _read(args.base)
    try:
        result = merge_changelogs(base, _read(args.ours), _read(args.theirs), profile)
    except MergeConflict as error:
        print(f"CONFLICT: {error}", file=sys.stderr)
        return 2
    issues = validate_text(result, profile, base_text=base)
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        return 2
    _write(args.output, result)
    print(f"MERGED: {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ph-changelog",
        description="Deterministic changelog inspection, validation, mutation, and merge tooling",
    )
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        help="bundled profile name or JSON file (default: %(default)s)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="validate changelog structure and policy")
    check.add_argument("path", nargs="?", default="CHANGELOG.md")
    check.add_argument("--base")
    check.set_defaults(func=cmd_check)

    inspect = subparsers.add_parser(
        "inspect",
        help="deconstruct a local changelog or stdin into versioned JSON",
    )
    inspect.add_argument(
        "path", nargs="?", default="CHANGELOG.md", help="file path or '-' for stdin"
    )
    inspect.add_argument("--output", default="-", help="JSON file path or '-' for stdout")
    inspect.set_defaults(func=cmd_inspect)

    normalize = subparsers.add_parser("normalize", help="normalize Unreleased sections")
    normalize.add_argument("path", nargs="?", default="CHANGELOG.md")
    normalize.add_argument("--write", action="store_true")
    normalize.set_defaults(func=cmd_normalize)

    add = subparsers.add_parser("add", help="insert structured Unreleased entries")
    add.add_argument("path", nargs="?", default="CHANGELOG.md")
    add.add_argument("--section")
    add.add_argument("--entry")
    add.add_argument("--entry-file")
    add.add_argument("--input", help="JSON operation file")
    add.add_argument("--breaking", action="store_true")
    add.add_argument("--write", action="store_true")
    add.set_defaults(func=cmd_add)

    merge = subparsers.add_parser("merge", help="merge additive Unreleased changes")
    merge.add_argument("base")
    merge.add_argument("ours")
    merge.add_argument("theirs")
    merge.add_argument("--output", required=True)
    merge.set_defaults(func=cmd_merge)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (ValueError, OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
