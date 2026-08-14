"""Bounded agent support for :mod:`ph_changelog`."""

from .apply import (
    ChangelogSnapshot,
    StaleChangelogError,
    apply_agent_output,
    atomic_write_if_unchanged,
    read_changelog_snapshot,
)
from .contracts import (
    ContractError,
    FactsError,
    validate_agent_output,
    validate_facts,
    validate_target_sections,
)
from .prompt import build_prompt

__all__ = [
    "ChangelogSnapshot",
    "ContractError",
    "FactsError",
    "StaleChangelogError",
    "apply_agent_output",
    "atomic_write_if_unchanged",
    "build_prompt",
    "read_changelog_snapshot",
    "validate_agent_output",
    "validate_facts",
    "validate_target_sections",
]

__version__ = "0.1.0"
