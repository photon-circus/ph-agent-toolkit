"""Command-line entry point for the bounded changelog agent."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from ph_changelog.profile import Profile, load_profile

from .apply import (
    StaleChangelogError,
    apply_agent_output,
    atomic_write_if_unchanged,
    read_changelog_snapshot,
)
from .contracts import ContractError, validate_agent_output, validate_target_sections
from .prompt import build_prompt
from .providers.lm_studio import call_lm_studio


def generate_output(
    facts: dict[str, Any],
    changelog_text: str,
    profile: Profile,
    *,
    skill_dir: str | Path | None = None,
    model: str = "coder",
    base_url: str | None = None,
    temperature: float = 0.1,
) -> dict[str, Any]:
    validate_target_sections(facts, set(profile.allowed_sections))
    system, user = build_prompt(facts, changelog_text, skill_dir)
    output = call_lm_studio(
        system,
        user,
        model=model,
        base_url=base_url,
        temperature=temperature,
    )
    validate_agent_output(output, facts, set(profile.allowed_sections))
    return output


def _read_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_bytes().decode("utf-8"))
    if not isinstance(value, dict):
        raise ContractError(f"{path} must contain a JSON object")
    return value


def cmd_facts_check(args: argparse.Namespace) -> int:
    profile = load_profile(args.profile)
    validate_target_sections(_read_json(args.path), set(profile.allowed_sections))
    print(f"OK: {args.path}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    profile = load_profile(args.profile)
    facts = _read_json(args.facts)
    snapshot = read_changelog_snapshot(args.path)
    output = generate_output(
        facts,
        snapshot.text,
        profile,
        skill_dir=args.skill_dir,
        model=args.model,
        base_url=args.base_url,
        temperature=args.temperature,
    )
    print(json.dumps(output, indent=2, ensure_ascii=False))

    # Escalation is an expected result, not an apply error. In particular, do
    # not call the application layer when --apply was supplied.
    if output["status"] == "needs_supervisor":
        return 3
    if args.apply:
        updated = apply_agent_output(snapshot.text, output, facts, profile)
        atomic_write_if_unchanged(args.path, snapshot, updated)
        print(f"APPLIED: {args.path}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ph-changelog-agent",
        description="Bounded changelog prose worker backed by LM Studio",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="generate validated changelog prose")
    run.add_argument("--facts", required=True)
    run.add_argument("--path", default="CHANGELOG.md")
    profile_default = os.environ.get("PH_CHANGELOG_PROFILE", "photon-circus")
    run.add_argument(
        "--profile",
        default=profile_default,
        help="core profile name or JSON path (default: photon-circus)",
    )
    run.add_argument(
        "--skill-dir",
        default=None,
        help="skill override (otherwise PH_CHANGELOG_SKILL_DIR or bundled assets)",
    )
    run.add_argument("--model", default=os.environ.get("LOCAL_CHANGELOG_MODEL", "coder"))
    run.add_argument("--base-url", default=None)
    run.add_argument("--temperature", type=float, default=0.1)
    run.add_argument("--apply", action="store_true")
    run.set_defaults(func=cmd_run)

    facts = subparsers.add_parser("facts", help="validate supervisor facts")
    facts_subparsers = facts.add_subparsers(dest="facts_command", required=True)
    check = facts_subparsers.add_parser("check")
    check.add_argument("path")
    check.add_argument(
        "--profile",
        default=os.environ.get("PH_CHANGELOG_PROFILE", "photon-circus"),
        help="core profile name or JSON path (default: photon-circus)",
    )
    check.set_defaults(func=cmd_facts_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (
        ContractError,
        StaleChangelogError,
        ValueError,
        OSError,
        json.JSONDecodeError,
        KeyError,
        IndexError,
        TypeError,
    ) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
