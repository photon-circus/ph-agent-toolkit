# Experiment lifecycle

`ph-agent-toolkit` is a source-only incubator for exploring agent boundaries.
Every artifact and implementation in this repository remains **experimental**,
regardless of lifecycle stage.

Stages describe the state of the work, not its safety, correctness, stability,
or production readiness.

## Stages

| Stage | Meaning |
| --- | --- |
| `proposed` | A boundary question or hypothesis has been recorded. No implementation or result is implied. |
| `experiment` | The proposal is being exercised through code, cases, proposals, or observations. Results may change the design. |
| `decision-needed` | Observations have exposed a working design choice that must be made or revisited. No decision is implied yet. |
| `concluded` | Active investigation has stopped with an outcome of supported, refuted, or inconclusive, and any working decision has been recorded. This is not certification. |
| `archived` | The record is retained for history but is not active guidance. New work should normally use a new experiment ID. |

Stages need not form a one-way sequence. A decision-needed experiment may
return to active experimentation when a counterexample or unresolved question
requires more evidence.

## Transition requirements

- `proposed` -> `experiment`: define the boundary, non-guarantees, and at least
  one planned success or refusal case.
- `experiment` -> `decision-needed`: link the observations that expose the
  choice and open an Experimental Decision Record (EDR).
- `experiment` -> `concluded`: record whether the hypothesis was supported,
  refuted, or remained inconclusive when no design decision is needed.
- `decision-needed` -> `experiment`: record the uncertainty or counterexample
  requiring more work.
- `decision-needed` -> `concluded`: record the working decision in an EDR,
  remaining risks, and follow-up questions.
- `concluded` -> `archived`: ensure links remain usable and the retained record
  contains only reviewed, sanitized material.

If a committed record is found to contain a secret, stop the normal lifecycle
transition. Revoke or rotate the secret immediately, follow the applicable
incident and Git-history-removal process, and archive only after the retained
record has been sanitized. Removing a secret from the current tree does not
remove it from history.

A passing test, model response, digest, or reviewer approval must not promote
an experiment automatically.

## Assurance language

Use precise, scoped language:

- "accepted by these cases," not "safe";
- "contract-checked," not "factually verified";
- "observed at this revision," not "proven";
- "working decision," not "production-ready."

Digests identify bytes. Tests demonstrate behavior under stated conditions.
Neither establishes semantic truth, authenticity, or universal safety.

## Repository records

Experiments live under [`experiments/`](../experiments/README.md). Working
design choices live under [`docs/decisions/`](decisions/README.md).

Lifecycle transitions are ordinary reviewed source changes. Git history
records who changed a record, but it is not an attestation system.
