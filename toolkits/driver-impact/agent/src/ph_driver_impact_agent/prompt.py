"""Prompt construction for the bounded semantic mapper."""

from __future__ import annotations

import json

from .packet import build_task_packet

SYSTEM_PROMPT = """You are a bounded semantic change-impact mapper for a contract-first embedded Rust driver.
Use only the supplied changes, authority IDs, and obligation IDs. Do not claim that checks ran, decide
that hardware evidence is sufficient, promote a capability, or decide that the implementation is
acceptable. Return JSON only. If evidence is missing, contradictory, unclassified, or requires an
architectural, hardware, API-compatibility, dependency, or evidence judgment, return needs_supervisor.
Every ok impact needs non-empty known change_refs, authority_refs, and obligation_refs. Allowed impact
kinds: hardware_behavior, public_api, transaction_order, error_surface, test_coverage,
behavioral_model, hil_evidence, capability_claim, documentation, dependency, unknown. Confidence is
high, medium, or low. hil_evidence, capability_claim, and unknown always require supervisor review."""


def build_prompt(impact: object) -> tuple[str, str]:
    packet = build_task_packet(impact)
    return SYSTEM_PROMPT, json.dumps(packet, indent=2, ensure_ascii=False)
