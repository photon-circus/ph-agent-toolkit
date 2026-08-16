"""CLI for deterministic driver change-impact inspection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .git import atomic_write, relative_output, repository_root
from .inspect import InspectionError, inspect_repository
from .profile import load_profile
from .render import render_json, render_summary


def cmd_inspect(args: argparse.Namespace) -> int:
    profile = load_profile(args.profile)
    repository = Path(args.repo)
    excluded: set[str] = set()
    root = repository_root(repository)
    output_relative = relative_output(root, args.output)
    if output_relative:
        output_path = Path(args.output)
        authority_paths = {document["path"] for document in profile.documents}
        if output_relative in authority_paths:
            raise ValueError("--output must not overwrite an authority document")
        if output_path.exists():
            try:
                existing = json.loads(output_path.read_bytes().decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ValueError(
                    "existing in-repository --output is not a driver-impact report"
                ) from error
            if not isinstance(existing, dict) or existing.get("task") != "driver_change_impact":
                raise ValueError("existing in-repository --output is not a driver-impact report")
        excluded.add(output_relative)
    document = inspect_repository(
        repository,
        profile,
        base=args.base,
        target=args.target,
        excluded_paths=excluded,
    )
    rendered = render_summary(document) if args.format == "summary" else render_json(document)
    if args.output == "-":
        sys.stdout.buffer.write(rendered.encode("utf-8"))
    else:
        atomic_write(args.output, rendered.encode("utf-8"))
    return 0 if document["result"]["status"] == "clear" else 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ph-driver-impact",
        description="Read-only impact inspection for contract-first driver repository changes",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect = subparsers.add_parser("inspect", help="inspect a local Git comparison")
    inspect.add_argument("--repo", default=".", help="path inside the local Git repository")
    inspect.add_argument("--base", default="HEAD", help="local base revision (default: HEAD)")
    inspect.add_argument(
        "--target",
        default="worktree",
        help="local target revision or 'worktree' (default: worktree)",
    )
    inspect.add_argument(
        "--profile",
        default="photon-circus-driver-v1",
        help="built-in profile name or JSON path",
    )
    inspect.add_argument("--format", choices=("json", "summary"), default="json")
    inspect.add_argument("--output", default="-", help="output path or '-' for stdout")
    inspect.set_defaults(func=cmd_inspect)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (InspectionError, ValueError, OSError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
