# Problem analysis brief harness cases

These are planned fixtures for the `problem-analysis-brief-harness` experiment.
They define the minimum observable success and refusal behavior before model or
provider orchestration is considered.

Every case remains experimental. Acceptance means only that the current
contract and implementation handled the fixture as described.

## Case conventions

Each implemented case should retain:

- the exact input bundle;
- the expected disposition: `accept`, `refuse`, or `accept-non-ready`;
- the expected diagnostic code or rendered artifact;
- the command used;
- the implementation commit tested;
- the observed result; and
- an explicit nonclaim.

Do not commit raw model transcripts or private source material. Hand-authored
fixtures are sufficient for the first slice.

## PA-001 — value-centred problem framing

**Purpose:** prove the complete accepted path.

The original statement should contain an embedded solution, for example:

> We keep implementing IIR filters differently. Build a reusable `ph-iir`
> crate.

The structured analysis must preserve the statement while separating:

- the observed repeated work;
- the proposed repository and mechanism;
- the affected consumers;
- the desired valuable condition;
- material assumptions and unknowns;
- risks of acting and not acting;
- a recommended next analytical step; and
- actions not authorized by the framing decision.

**Expected disposition:** `accept`.

**Expected effects:** emit a validation result and a rendered Problem Analysis
Brief. The brief must lead with the decision and value surfaces and place the
technical annex later.

**Nonclaim:** the case does not establish that the analysis or recommendation is
correct.

## PA-002 — unknown or mistyped field

Add one unrecognized field at a nested level where the contract is closed.

**Expected disposition:** `refuse`.

**Expected effects:** report the exact path and unknown field; emit no brief.

**Purpose:** prove the contract does not silently ignore model or operator
output.

## PA-003 — dangling record or evidence reference

Reference a consumer, proposition, source, risk, or finding identifier that is
not present in the bundle.

**Expected disposition:** `refuse`.

**Expected effects:** report the referencing field and missing identifier; emit
no brief.

**Purpose:** prove traceability is structurally inspectable.

## PA-004 — decision request exceeds the current gate

At the `problem-framing` gate, request authorization to create a repository,
implement a solution, publish a package, or perform another forbidden action.

**Expected disposition:** `refuse`.

**Expected effects:** identify the requested action and the gate's permitted
decision set; emit no brief.

**Purpose:** prove that a model-produced or hand-authored field cannot expand
its own authority.

## PA-005 — required value surface absent

Supply detailed technical analysis but omit the named consumer, valuable effect,
or material trade-off required by the brief contract.

**Expected disposition:** `refuse` when the brief is marked ready for human
review.

**Expected effects:** identify the missing value-surface fields; emit no ready
brief.

**Purpose:** prove technical detail cannot satisfy the brief contract by volume.

**Nonclaim:** the check does not prove that supplied value language is
meaningful.

## PA-006 — unresolved blocking challenge marked ready

Include a blocking challenge finding with no accepted disposition while marking
the brief `ready-for-human-review`.

**Expected disposition:** `refuse`.

**Expected effects:** identify the blocking finding and inconsistent readiness
state; emit no ready brief.

**Purpose:** prove the synthesis cannot hide a challenge by changing a status
field.

## PA-007 — honest partial analysis

Include explicit unknowns, a material assumption with consequence-if-false and
re-examination trigger, and one unresolved non-blocking challenge. Mark the
brief `draft` or `challenged` and request only bounded reconnaissance or framing
review.

**Expected disposition:** `accept-non-ready`.

**Expected effects:** render a brief that keeps the uncertainty and
non-authorization visible.

**Purpose:** prove missing information is not automatically converted into
failure, approval, or assigned work.

## PA-008 — deterministic repeat render

Run the renderer twice against the same accepted input bytes and implementation
revision.

**Expected disposition:** `accept`.

**Expected effects:** rendered output bytes are identical.

**Purpose:** establish only the tested deterministic rendering property.

**Nonclaim:** byte identity does not establish factual or semantic correctness.

## Guard verification rule

For every refusal case, the implementation work should begin from an accepted
fixture, inject the exact invalid condition, observe refusal, then restore the
fixture. A test that merely asserts an error type without demonstrating that the
intended guard is reachable is insufficient evidence for the experiment.
