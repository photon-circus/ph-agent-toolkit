# Agent orientation: problem analysis brief harness

> [!WARNING]
> This is an orientation for a proposed experiment inside a living, source-only
> incubator. It is not an implementation authorization, product specification,
> compatibility promise, or release plan. Read the repository's
> [`STATUS.md`](../../STATUS.md) before using this document.

## 1. Handoff objective

Orient a later coding agent to develop the **first bounded experimental slice**
of a local problem-analysis harness.

The eventual user experience being explored is:

> A maintainer states a problem or asks a question in ordinary language. A
> supervised process preserves that statement, decomposes the analysis through
> bounded roles, challenges the resulting reasoning, and produces a
> standardized brief that presents the value at stake, available decisions,
> risks, and recommendation before the supporting technical analysis.

This orientation does **not** ask the next agent to build that complete system.
The first implementation question is much narrower:

> Can a deterministic, offline core validate a manually curated analysis bundle
> and render a stable, value-centred Problem Analysis Brief without importing a
> model, prompt, provider, network client, or autonomous decision mechanism?

The first slice exists to test the artifact and authority boundary. Agent
orchestration is deferred until that boundary is useful under explicit success
and refusal cases.

## 2. Required reading, in order

Before proposing or changing code, read:

1. [`STATUS.md`](../../STATUS.md)
2. [`AGENTS.md`](../../AGENTS.md)
3. [`docs/EXPERIMENT_LIFECYCLE.md`](../../docs/EXPERIMENT_LIFECYCLE.md)
4. [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
5. [`experiments/README.md`](../README.md)
6. [`README.md`](README.md) in this experiment
7. [`cases/README.md`](cases/README.md)
8. the changelog toolkit's core package structure and tests as repository-local
   examples, without copying its domain model blindly

When this orientation conflicts with an owning repository document, the owning
repository document controls. Report the conflict rather than selecting the
wording that makes implementation easiest.

## 3. Why this belongs in `ph-agent-toolkit`

This work is primarily an experiment in **authority, evidence, artifact, and
model boundaries**:

- a human supplies a problem and retains all decision authority;
- agents may later propose structured analysis records;
- deterministic code owns shape, reference, state, authorization, and rendering
  checks;
- technical depth supports rather than replaces the decision surface;
- every conclusion remains traceable to classified records and sources; and
- no model response, successful parse, or green test authorizes action.

That fits the incubator's current purpose. The experiment must not be described
as a supported planning product or as destined for publication. If repeated
experiments later establish a stable, separately useful capability, extraction
would require another owner decision and a separately named repository.

## 4. Product and communication principle under test

The brief is not a technical report with an executive summary added afterward.
Its decision surface is primary.

The first screen or opening sections should answer:

1. What decision is required now?
2. What value or useful condition is at stake, and for whom?
3. What current condition prevents that value?
4. What effect should be created without presuming the implementation?
5. What principal risks, costs, and continuing obligations matter?
6. What is recommended?
7. What evidence or changed assumption would alter that recommendation?
8. What is explicitly not authorized by this decision?

Technical architecture, Rust constraints, target analysis, repository fit,
numeric evidence, implementation mechanisms, and detailed source records follow
as analytical support.

### 4.1 Value statement form

A useful value statement normally has the shape:

> `<consumer>` can `<valuable outcome>` under `<important conditions>`, reducing
> `<cost, risk, inconsistency, or delay>` while accepting `<material trade-off
> or continuing obligation>`.

Example:

> Embedded project maintainers can reuse one bounded filtering behavior across
> products, reducing repeated numeric design and inconsistent claims while
> accepting a durable verification and compatibility obligation.

### 4.2 Risk statement form

A useful risk record normally identifies:

- the uncertain condition;
- the consequence if it occurs;
- the present basis for likelihood or uncertainty;
- possible mitigation or information-gathering;
- the trigger for re-examination.

### 4.3 Recommendation form

A useful recommendation normally states:

- the valuable direction;
- the named consumer and principal benefit;
- accepted cost and residual risk;
- reversibility or lock-in;
- the next decision being requested; and
- downstream actions that remain unauthorized.

### 4.4 Mechanism is not the headline

Avoid headline decisions such as:

> Create `ph-iir` with Q-format biquads and a host-side coefficient generator.

Prefer:

> Standardize deterministic embedded filtering so projects stop re-solving
> numeric behavior and can make consistent, supportable claims.

The technical annex may then describe a runtime crate, restricted filter forms,
fixed-point analysis, or host tooling as candidate mechanisms.

## 5. Authority boundary

### 5.1 Human supervisor retains

- acceptance or revision of the problem framing;
- authorization of reconnaissance or course-of-action development;
- repository admission and naming;
- contract adoption and mutation;
- compatibility, lifecycle, visibility, exception, publication, and release
  decisions;
- acceptance of residual risk; and
- any irreversible action.

### 5.2 Deterministic core may own

- versioned input contracts;
- closed-field validation;
- identifier uniqueness and reference resolution;
- artifact classification and state checks;
- gate and authorization checks;
- explicit readiness/refusal rules;
- stable rendering order;
- local diagnostics;
- local output to an explicitly selected path; and
- serialization and byte-identity observations defined by the experiment.

### 5.3 A later agent layer may propose

- problem restatements;
- consumer and value records;
- source-derived propositions;
- assumptions, unknowns, causes, and risks;
- challenge findings;
- preliminary recommendations; and
- brief fields expressed through the validated contract.

That later layer must not mutate the target artifact directly or bypass core
validation.

### 5.4 Neither core nor agent may infer authority

A record stating `recommended`, `accepted`, `ready`, or `approved` has no effect
unless the contract identifies the human decision and the current gate permits
that state. The first slice should not implement approval or repository actions
at all.

## 6. First implementation slice

### 6.1 Provisional capability path

If the orientation is accepted, the expected repository location is:

```text
toolkits/problem-analysis/
  core/
    README.md
    pyproject.toml
    src/ph_problem_analysis/
    tests/
  examples/
```

Provisional distribution and command names are:

```text
ph-problem-analysis
ph_problem_analysis
```

These names are experimental coordinates, not compatibility commitments. If a
material naming or responsibility conflict is found, stop and propose a change
rather than silently broadening or renaming the capability.

Do **not** create `agent/` or `remote/` in the first slice.

### 6.2 Required commands

The smallest useful command surface is:

```text
ph-problem-analysis validate <bundle.json>
ph-problem-analysis render <bundle.json> --output <brief.md>
```

An `inspect` command that emits a normalized machine view may be added only if
it directly helps tests or supervised review. Do not add orchestration, model,
research, GitHub, Notion, repository-generation, or workflow commands.

### 6.3 Single closed bundle, not a workflow engine

Use one versioned, closed JSON document for the first slice. The experiment may
later show that a multi-file run workspace is necessary, but it should not be
assumed now.

A provisional top-level shape is:

```json
{
  "schema_version": "problem-analysis-bundle/v1",
  "run": {},
  "intake": {},
  "gate": {},
  "records": {},
  "challenge": {},
  "brief": {}
}
```

The exact nested field design is part of the first implementation proposal, but
it must remain limited to records needed by the initial cases. Do not encode the
complete future operational-planning lifecycle.

### 6.4 Minimum record concepts

The first bundle should represent only what the Problem Analysis Brief needs:

- **run identity** — an opaque local identifier and contract version;
- **intake** — exact original statement bytes or a lossless UTF-8 field plus a
  core-computed digest;
- **current gate** — problem framing, with an explicit set of decisions that
  may be requested;
- **consumer records** — who experiences the condition and what value is
  absent;
- **proposition records** — classified as observation, report, inference,
  assumption, or unknown;
- **source references** — enough identity to resolve references inside the
  bundle, without claiming source authenticity;
- **risk records** — action, inaction, or analytical risk;
- **challenge findings** — severity, status, affected record, and disposition;
- **brief readiness** — draft, challenged, ready-for-human-review, or refused;
- **brief content** — structured fields rendered in the prescribed order; and
- **authorization boundary** — requested decision and actions explicitly not
  authorized.

Do not add course-of-action, campaign, implementation-graph, release, or task
records to the first contract.

### 6.5 Classification discipline

The contract should keep these meanings separate:

| Classification | Meaning |
| --- | --- |
| `observation` | Directly observed in an identified artifact, run, repository, or physical setup |
| `report` | Asserted by a person or external record but not independently reproduced here |
| `inference` | Reasoned from other records; supporting references and uncertainty remain visible |
| `assumption` | Temporarily accepted for planning; includes consequence if false and a re-examination trigger |
| `unknown` | Not currently established; does not automatically create a work assignment |

Do not call a statement a `fact` merely because an agent found a source. If the
first contract uses `fact`, define it narrowly as an established proposition
with explicit source support and retain the source and evidence limitation.

### 6.6 Gate and authorization model

The first slice has one gate: `problem-framing`.

Permissible decision requests may include:

- approve the restated problem;
- revise the problem or boundary;
- authorize bounded reconnaissance;
- authorize later course-of-action development;
- defer;
- reject; or
- retain as referential analysis.

It must not request or imply authorization to:

- create a repository;
- implement a solution;
- adopt an architecture or compatibility contract;
- tag, publish, release, deploy, or qualify anything.

The core should reject a bundle whose requested decision exceeds the gate's
allowed decisions.

## 7. Standard Problem Analysis Brief contract

The renderer controls the following order:

1. **Decision required**
2. **Value at stake**
3. **Problem as understood**
4. **Current condition**
5. **Desired effect**
6. **Why this matters now**
7. **Key findings**
8. **Material assumptions and unknowns**
9. **Risks of action and inaction**
10. **Recommended next analytical step**
11. **What would change the recommendation**
12. **Decision requested**
13. **Explicit non-authorization**
14. **Analytical summary**
15. **Technical annex**
16. **Sources, traceability, and unresolved findings**

A bundle may leave optional analytical detail empty only where the contract
permits it. It may not omit the decision, value, risk, recommendation,
change-condition, decision-request, or non-authorization surfaces and still be
marked ready.

### 7.1 Deterministic checks versus semantic judgment

The core can require a `value_at_stake` field and place it before technical
analysis. It cannot prove that the value statement is meaningful.

The core can require risks to identify consequence and uncertainty. It cannot
prove that likelihood is estimated correctly.

The core can require every recommendation to name a benefit, trade-off,
residual risk, and next decision. It cannot decide whether the recommendation
is wise.

Do not implement keyword scoring or claim that technical language has been
semantically subordinated. Prefer structural checks, controlled rendering, and
human-visible diagnostics.

## 8. Required validation and refusal behavior

The first implementation should fail closed on:

- unsupported schema version;
- missing required or unknown fields;
- duplicate identifiers;
- dangling references;
- references to explicitly superseded or unavailable records where the contract
  requires current records;
- an observation or established proposition with no source or evidence
  reference when one is required;
- a material assumption missing consequence-if-false or re-examination trigger;
- a recommendation missing benefit, trade-off, residual risk, or
  change-condition;
- a requested decision outside the current gate;
- a brief marked ready while a blocking challenge finding remains unresolved;
- a technical annex present without a decision and value surface; and
- an output path that is the input path or another path the command did not
  explicitly receive.

The first implementation should permit honest partial analysis when:

- unknowns are explicitly classified;
- uncertainty is visible in the brief;
- readiness remains draft or challenged where appropriate;
- no missing information is represented as approval; and
- the decision requested remains proportional to the available evidence.

A warning is not a substitute for refusal when a contract or authority boundary
is violated.

## 9. Planned cases

Implement the cases in [`cases/README.md`](cases/README.md) as reviewed fixtures.
At minimum:

- one accepted end-to-end bundle and golden rendered brief;
- unknown-field refusal;
- dangling-reference refusal;
- over-authorized decision refusal;
- missing value surface refusal;
- unresolved blocking finding refusal;
- honest partial analysis accepted as non-ready; and
- repeat rendering with byte-identical output.

For each guard, deliberately break the accepted fixture and prove the check
fails before restoring it. A guard that has never been observed refusing its
intended case is not yet useful evidence.

## 10. Package and dependency constraints

- Python 3.11 or later, consistent with the workspace.
- Prefer the standard library.
- No runtime dependency without a concrete contract benefit and explicit
  rationale.
- Retain the `Private :: Do Not Upload` classifier.
- Join the root uv workspace only when implementation begins.
- Use installed console commands and `uv run --locked` in documentation and
  tests.
- The core must import no agent, prompt, model, provider, HTTP, GitHub, or Notion
  module.
- The first slice requires no remote adapter.

If closed JSON validation cannot be implemented cleanly without a dependency,
present the options and trade-off before adding one. Do not write an incomplete
validator and describe it as schema validation.

## 11. Expected first implementation deliverables

A bounded first implementation pull request should contain:

1. the proposed `toolkits/problem-analysis/core` package;
2. a package README stating responsibility, current commands, refusal behavior,
   and non-guarantees;
3. one explicit versioned bundle contract, implemented in code and documented;
4. deterministic validation and Markdown rendering;
5. the two required command surfaces;
6. accepted and refusal fixtures under the experiment dossier or toolkit
   examples, with one canonical owner for each fixture;
7. unit and CLI tests for every success and refusal case;
8. workspace and lockfile updates;
9. root and toolkit documentation updates required by the changed command and
   package surfaces;
10. a changelog entry under `[Unreleased]`; and
11. an update to this experiment dossier proposing `proposed` -> `experiment`
    only if the transition requirements are actually met.

Do not add an agent package, multi-agent scheduler, prompt assets, provider
adapter, web search, repository scanner, Notion integration, GitHub mutation,
course-of-action engine, campaign graph, or autonomous implementation planner.

## 12. Recommended implementation sequence

1. **Restate the bounded responsibility.** Confirm that the first core owns only
   contract validation and rendering of a manually curated Problem Analysis
   Brief bundle.
2. **Write the fixture contract first.** Draft `PA-001` and the refusal fixtures
   before selecting classes or modules.
3. **Define closed types and diagnostics.** Make every accepted and refused
   state explicit.
4. **Implement pure validation.** No filesystem writes beyond CLI input reads.
5. **Implement rendering from accepted data.** Keep rendering free of semantic
   inference.
6. **Add CLI wrappers.** Parse arguments, call core operations, and report
   distinct validation versus I/O failures.
7. **Prove each refusal.** Inject the fault and observe the failure.
8. **Integrate with the uv workspace.** Update lockfile only after package
   boundaries are coherent.
9. **Run every repository check.** Include all existing toolkit suites; do not
   test only the new package.
10. **Update the experiment record.** State what was observed and what remains
    unproven.

## 13. Stop and escalate when

Stop implementation and return a decision request if:

- the core appears to need model judgment to validate a record;
- useful operation requires network access or repository mutation;
- the bundle begins encoding the complete future lifecycle rather than the
  first brief;
- a multi-file state engine becomes necessary before the single-bundle cases
  have been exercised;
- the package responsibility overlaps materially with the changelog toolkit;
- a dependency is needed primarily for convenience rather than a contract
  benefit;
- honest uncertainty cannot be represented without weakening refusal behavior;
- the value-first requirement can only be approximated through brittle keyword
  checks;
- the implementation would allow a model-produced field to authorize an action;
  or
- the requested work would describe the experiment as trusted, stable,
  supported, secure, production-ready, or intended for publication.

## 14. Deferred work

The following are plausible later experiments, not requirements for the first
slice:

- a multi-file run workspace with artifact supersession and resumability;
- source-intake and provenance adapters;
- bounded role prompts and skill packages;
- provider-neutral agent adapters;
- multiple independent analytical lanes;
- challenge-context construction;
- finding disposition workflows;
- course-of-action and decision briefs;
- campaign briefs and implementation graphs;
- GitHub or Notion read integrations;
- supervisor dashboards;
- extraction into a supported repository.

Each should be admitted only when a current consumer and experiment requires it.

## 15. Required checks

From the workspace root, run at least:

```bash
uv sync --all-packages --locked
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked python -m unittest discover -s toolkits/changelog/core/tests -v
uv run --locked python -m unittest discover -s toolkits/changelog/agent/tests -v
uv run --locked python -m unittest discover -s toolkits/changelog/remote/tests -v
```

Add the new package's test command once the package exists. Record any command
that could not run and why. Passing checks are regression evidence for the
cases that ran, not assurance of decision quality.

## 16. Definition of done for the first slice

- [ ] One closed bundle contract is documented and implemented.
- [ ] The exact original problem statement is retained and byte-identified.
- [ ] Core is offline and imports no agent, prompt, provider, or network code.
- [ ] Accepted input renders the prescribed value-first brief order.
- [ ] Technical analysis appears after the decision, value, risk, and
      recommendation surfaces.
- [ ] Unknown fields, dangling references, and authority escalation fail closed.
- [ ] Honest unknowns can remain visible without becoming implicit work or
      approval.
- [ ] A ready brief cannot retain an unresolved blocking challenge finding.
- [ ] Identical accepted input produces identical rendered bytes in the tested
      environment.
- [ ] Every required refusal guard has been deliberately observed firing.
- [ ] Public wording preserves the incubator's experimental, source-only trust
      posture.
- [ ] The experiment dossier identifies the exact evidence obtained and the
      properties not established.
- [ ] No implementation, repository, lifecycle, release, or publication
      authority is inferred from the result.

## 17. Handoff instruction for the next agent

Use the following as the bounded assignment:

> Read the repository authority and experiment documents listed in this
> orientation. Review the proposed `problem-analysis-brief-harness` boundary and
> produce an implementation plan for the first **core-only** slice. The plan
> must begin from the required success and refusal fixtures, identify the closed
> bundle contract, deterministic validation and rendering responsibilities,
> package layout, tests, workspace changes, and coupled documentation edits.
> Do not add an agent package, provider, network access, autonomous research,
> repository mutation, course-of-action machinery, or release behavior. Do not
> implement until you have identified any contradiction or premature contract
> in this orientation. Treat value, risk, and decision wording as human-reviewed
> semantic content; enforce only inspectable structure, references, gate
> authority, readiness, and rendering order in deterministic code. Return any
> boundary decision as an explicit question rather than silently resolving it.

The next agent's first output should be a reviewable plan and identified
contract questions, not code.
