# Experiment: problem analysis brief harness

| Field | Value |
| --- | --- |
| ID | `problem-analysis-brief-harness` |
| Stage | `proposed` |
| Assurance | `experimental` |
| Owner | Photon Circus maintainer acting as supervisor |
| Related boundaries | [`STATUS.md`](../../STATUS.md), [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md), [`AGENT_ORIENTATION.md`](AGENT_ORIENTATION.md) |
| Related EDRs | none |
| Implementation references | none; this dossier and its orientation do not authorize implementation |

## Question

Can a supervised, local, source-only toolkit turn an ordinary-language problem
statement into a traceable and standardized **Problem Analysis Brief** while:

- keeping the original statement intact;
- separating observations, reports, inferences, assumptions, and unknowns;
- leading with consumer value, risk, cost, and the decision required;
- placing technical analysis in supporting sections rather than using technical
  mechanisms as the decision headline;
- making challenge findings and unresolved uncertainty visible; and
- retaining every planning, repository, implementation, and release decision
  with the human supervisor?

## Hypothesis

A deterministic, offline core can validate a manually curated, closed analysis
bundle and render a stable Problem Analysis Brief without importing a model,
provider, prompt, or network dependency. If that contract is useful under
success and refusal cases, a later agent layer can propose the same structured
records without gaining authority over validation, rendering, or decisions.

The smallest useful result is not an autonomous planning system. It is a local
command that accepts one versioned analysis bundle, rejects invalid authority or
reference states, and renders one value-centred brief whose technical annex is
explicitly subordinate to the decision surface.

## Counter-hypothesis

The experiment should be reconsidered if one or more of the following is
observed:

- the proposed record model encodes speculative process rather than recurring
  analytical needs;
- value-centred briefing depends on semantic judgment that deterministic checks
  can only imitate through ceremonial keyword rules;
- the core must import model, provider, prompt, or network code to be useful;
- a single closed bundle cannot preserve enough provenance and revision context,
  but a multi-file workflow engine would be premature;
- validation makes honest partial analysis impossible by treating every unknown
  as an error; or
- a much smaller document template plus human review provides the same value.

## Boundary

| Concern | Definition |
| --- | --- |
| Authority holder | The human maintainer approves the problem framing, planning guidance, later course of action, and any implementation or release decision. |
| Trusted inputs | Only the exact bytes supplied as the supervisor's original statement are trusted as *the statement received*. Their factual content is not automatically trusted. Repository-owned contracts may be treated as authorities only when explicitly identified by the supervisor or a later source-intake step. |
| Untrusted inputs | Model output, agent analysis, external and repository sources, custom skills, examples, inferred facts, risk estimates, and rendered prose. |
| Allowed effects | The first core experiment may read an explicitly selected local bundle, validate it, report findings, and write a rendered brief only to an explicitly selected local output path. |
| Forbidden effects | Network or model calls; GitHub, Notion, repository, or source-document mutation; issue or repository creation; implementation planning; automatic approval; lifecycle, compatibility, publication, release, or qualification decisions. |
| Refusal or escalation | Refuse malformed or open contracts, duplicate or dangling identifiers, stale or superseded references, unauthorized decision requests, and a brief marked ready while unresolved blocking findings remain. Escalate semantic disagreements, unsupported factual claims, and decisions whose value or risk cannot be established mechanically. |

## Validation scope

### Deterministic checks

The first slice is expected to establish only inspectable contract properties:

- one supported schema version and no unknown fields;
- required fields and enumerated states;
- immutable preservation and digesting of the original intake bytes;
- unique record identifiers and resolvable references;
- explicit classifications for facts, reports, inferences, assumptions, and
  unknowns;
- evidence references for statements represented as established facts;
- consequence and re-examination fields for material assumptions;
- decision requests limited to the authority granted by the current gate;
- required value, risk, recommendation, and change-condition fields;
- a renderer-controlled section order that places technical analysis after the
  decision surface;
- visible unresolved findings and refusal to mark a brief ready while a blocking
  finding remains unresolved; and
- byte-identical rendering for the same accepted bundle and implementation
  revision.

### Semantic review

The following remain human or supervised-agent judgment:

- whether a cited source supports a proposition;
- whether the problem is real, recurrent, or material;
- whether the consumer and value statement are correct;
- whether a causal explanation is persuasive;
- whether a risk estimate is credible;
- whether technical analysis is sufficient;
- whether the recommendation is reasonable; and
- whether any planning or implementation activity should be authorized.

### Non-guarantees

- This experiment does not establish production readiness, factual truth,
  decision quality, security, prompt-injection resistance, or suitability for
  unattended use.
- Contract acceptance does not mean that the brief follows from its sources.
- A stable render does not make the content correct or authoritative.
- No package, schema, command, directory, or output format is a compatibility
  promise.
- This dossier does not authorize creation of the proposed toolkit package.

## Cases

Planned cases are defined in [`cases/README.md`](cases/README.md). At minimum,
the experiment requires one complete accepted case and refusal cases for an
open contract, dangling reference, authority escalation, technical-only
headline, and unresolved blocking challenge.

| Case | Expected disposition | Expected effects |
| --- | --- | --- |
| `PA-001` value-centred problem framing | accept | Validation report and rendered local brief |
| `PA-002` unknown or mistyped field | refuse | Diagnostic only; no brief |
| `PA-003` dangling evidence or record reference | refuse | Diagnostic only; no brief |
| `PA-004` decision request exceeds current gate | refuse | Diagnostic only; no brief |
| `PA-005` required value surface absent | refuse | Diagnostic only; no brief |
| `PA-006` unresolved blocker marked ready | refuse | Diagnostic only; no brief |
| `PA-007` honest partial analysis | accept with visible uncertainty | Rendered brief retains unknowns and non-authorization |
| `PA-008` repeat render | accept | Identical output bytes for identical accepted input |

## Proposal records

- [`AGENT_ORIENTATION.md`](AGENT_ORIENTATION.md) — self-contained orientation
  and bounded first-slice assignment for a later implementation agent.

Proposal records are reviewed design inputs, not implementation authority or
verified claims.

## Evidence and observations

None yet. This experiment remains `proposed`.

## Outcome

Not applicable at the `proposed` stage.

## Next transition

A later pull request may propose `proposed` -> `experiment` only after it:

1. preserves the boundary and non-guarantees above;
2. defines the first closed bundle contract before model orchestration;
3. supplies `PA-001` and the required refusal fixtures;
4. demonstrates that the deterministic core can run without an agent or network
   dependency; and
5. records what the checks do not establish.

A merge, green checks, or successful model output must not be represented as
concluding the experiment or authorizing a supported extracted project.
