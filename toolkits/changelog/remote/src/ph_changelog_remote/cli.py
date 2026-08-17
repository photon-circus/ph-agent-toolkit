"""CLI for an experimental remote-retrieval boundary."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from ph_changelog.machine import deconstruct_changelog, render_machine_json
from ph_changelog.profile import load_profile

from .fetch import DEFAULT_MAX_BYTES, DEFAULT_TIMEOUT, RemoteFetchError, fetch_changelog

DEFAULT_PROFILE = os.environ.get("PH_CHANGELOG_PROFILE", "photon-circus")


def _write_stdout(text: str) -> None:
    encoded = text.encode("utf-8")
    buffer = getattr(sys.stdout, "buffer", None)
    if buffer is None:
        sys.stdout.write(text)
    else:
        buffer.write(encoded)
        buffer.flush()


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


def cmd_fetch(args: argparse.Namespace) -> int:
    profile = load_profile(args.profile)
    result = fetch_changelog(
        args.url,
        timeout=args.timeout,
        max_bytes=args.max_bytes,
        allow_http=args.allow_http,
    )
    machine_document = deconstruct_changelog(result.raw, profile, result.source)
    rendered = render_machine_json(machine_document)
    if args.output == "-":
        _write_stdout(rendered)
    else:
        _write_atomic(args.output, rendered)
    return 0 if machine_document["validation"]["valid"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ph-changelog-remote",
        description="Experimentally fetch and deconstruct a remote changelog snapshot",
        epilog=(
            "INCUBATOR: not an SSRF defense or network sandbox. Use only operator-reviewed "
            "URLs and treat returned content as untrusted."
        ),
    )
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        help="bundled profile name or JSON file (default: %(default)s)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch = subparsers.add_parser(
        "fetch", help="fetch one operator-reviewed remote Markdown changelog"
    )
    fetch.add_argument("url", help="raw Markdown URL")
    fetch.add_argument("--output", default="-", help="JSON file path or '-' for stdout")
    fetch.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="overall retrieval deadline in seconds (default: %(default)s)",
    )
    fetch.add_argument(
        "--max-bytes",
        type=int,
        default=DEFAULT_MAX_BYTES,
        help="maximum response size (default: %(default)s)",
    )
    fetch.add_argument(
        "--allow-http",
        action="store_true",
        help="allow an initial plain HTTP URL (HTTPS downgrades remain forbidden)",
    )
    fetch.set_defaults(func=cmd_fetch)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (RemoteFetchError, ValueError, OSError, KeyError, TypeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
