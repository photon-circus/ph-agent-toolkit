"""CLI for the bounded local semantic-impact mapper."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from ph_driver_impact.git import atomic_write
from ph_driver_impact.machine import validate_impact_document

from .contracts import ContractError, validate_agent_output
from .packet import build_task_packet
from .prompt import build_prompt
from .providers.lm_studio import call_lm_studio
from .stale import StaleImpactError, verify_current


def _read_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_bytes().decode("utf-8"))
    if not isinstance(value, dict):
        raise ContractError(f"{path} must contain a JSON object")
    return value


def _emit(value: object, output: str) -> None:
    rendered = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if output == "-":
        sys.stdout.buffer.write(rendered)
    else:
        atomic_write(output, rendered)


def generate_output(
    impact: dict[str, Any],
    *,
    model: str,
    base_url: str | None = None,
    temperature: float = 0.1,
) -> dict[str, Any]:
    if impact["result"]["status"] == "clear":
        raise ContractError("clear impact document has no semantic mapping task")
    system, user = build_prompt(impact)
    output = call_lm_studio(
        system,
        user,
        model,
        base_url=base_url,
        temperature=temperature,
    )
    return validate_agent_output(output, impact)


def cmd_packet(args: argparse.Namespace) -> int:
    _emit(build_task_packet(_read_json(args.impact)), args.output)
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    validate_agent_output(_read_json(args.output_document), _read_json(args.impact))
    print(f"OK: {args.output_document}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    impact = _read_json(args.impact)
    validate_impact_document(impact)
    verify_current(impact, args.impact, args.profile)
    output = generate_output(
        impact,
        model=args.model,
        base_url=args.base_url,
        temperature=args.temperature,
    )
    verify_current(impact, args.impact, args.profile)
    _emit(output, args.output)
    return 3 if output["status"] == "needs_supervisor" else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ph-driver-impact-agent",
        description="Bounded local-model semantic mapping for driver impact documents",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    packet = subparsers.add_parser("packet", help="render the bounded model task packet")
    packet.add_argument("--impact", required=True)
    packet.add_argument("--output", default="-")
    packet.set_defaults(func=cmd_packet)

    check = subparsers.add_parser("check", help="validate saved model output")
    check.add_argument("--impact", required=True)
    check.add_argument("--output-document", required=True)
    check.set_defaults(func=cmd_check)

    run = subparsers.add_parser("run", help="request and validate semantic impact mapping")
    run.add_argument("--impact", required=True)
    run.add_argument("--profile", default=None, help="custom profile path used by the core")
    run.add_argument("--model", default=os.environ.get("LOCAL_DRIVER_IMPACT_MODEL", "coder"))
    run.add_argument("--base-url", default=None)
    run.add_argument("--temperature", type=float, default=0.1)
    run.add_argument("--output", default="-")
    run.set_defaults(func=cmd_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (ContractError, StaleImpactError, ValueError, OSError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
