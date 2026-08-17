# Experiment: <title>

| Field | Value |
| --- | --- |
| ID | `<experiment-id>` |
| Stage | `proposed` |
| Assurance | `experimental` |
| Owner | `<name or team>` |
| Related boundaries | `<links>` |
| Related EDRs | `none` |
| Implementation references | `<commits, paths, or none>` |

## Question

What boundary question is this experiment trying to answer?

## Hypothesis

State the smallest testable expectation.

## Counter-hypothesis

What plausible result would challenge the hypothesis?

## Boundary

| Concern | Definition |
| --- | --- |
| Authority holder | `<who or what may decide>` |
| Trusted inputs | `<explicitly trusted inputs>` |
| Untrusted inputs | `<model, repository, network, operator input, etc.>` |
| Allowed effects | `<reads, proposals, bounded writes, requests>` |
| Forbidden effects | `<effects this layer must not perform>` |
| Refusal or escalation | `<when work must stop>` |

## Validation scope

### Deterministic checks

- `<shape, digest, authority, mutation, or transport checks>`

### Semantic review

- `<claims that still require human or supervisor judgment>`

### Non-guarantees

- This experiment does not establish production readiness.
- `<additional properties not established>`

## Cases

| Case | Expected disposition | Expected effects |
| --- | --- | --- |
| `<case link>` | `accept`, `refuse`, or `escalate` | `<none or bounded effects>` |

## Proposal records

- `<links or none>`

Proposal records are contract-checked artifacts, not verified claims.

## Evidence and observations

- `<links or none>`

## Outcome

Use only when moving toward `concluded`:

- Result: `supported`, `refuted`, or `inconclusive`
- Scope: `<conditions under which the result was observed>`
- Remaining uncertainty: `<known gaps>`

## Next transition

State the proposed lifecycle transition and the record required before making
it. Valid stages are `proposed`, `experiment`, `decision-needed`, `concluded`,
and `archived`.
