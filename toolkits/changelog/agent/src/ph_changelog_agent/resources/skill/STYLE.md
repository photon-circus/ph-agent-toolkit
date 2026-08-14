# Photon Circus changelog style

The changelog is an integrator-facing engineering record, not a commit log.

## Canonical subsection order

1. Added
2. Changed
3. Deprecated
4. Fixed
5. Removed
6. Security
7. Documentation
8. Known issues

The local model does not place headings; this order is enforced by tooling.

## Entry content

A strong entry normally answers the subset that applies:

- What changed?
- What previous behavior or limitation matters?
- What behavior is now observable to the integrator?
- What important boundary remains?
- What supplied evidence supports a correctness, boundedness, performance, or concurrency claim?

Prefer concrete API/type names and explicit behavior over adjectives.

## Breaking changes

The deterministic tool adds the `**Breaking:**` marker when the supervisor marks
the task as breaking. Do not add or remove that classification yourself.

## Evidence discipline

Mention Loom, Miri, QEMU instruction measurements, code-size measurements, CI
gates, tests, or contracts only when they appear in `TASK_FACTS`.

## Avoid

- commit-by-commit narration;
- "miscellaneous changes" / "various fixes";
- unsupported adjectives such as "safe", "fast", "zero-cost", or "wait-free";
- implementation details that do not affect an integrator-facing behavior, cost, limitation, or reproducibility claim.
