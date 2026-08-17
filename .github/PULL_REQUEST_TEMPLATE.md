## Incubator status

This repository is a living, source-only concept incubator. A merged experiment
does not become trusted, supported, production-ready, or eligible for package
publication.

- [ ] I have not described this work as stable, safe, hardened, trusted,
      production-ready, or release-bound.
- [ ] Any words such as deterministic, bounded, atomic, validated, protected,
      or lossless are scoped to the exact mechanism and evidence that support
      them.

## Boundary hypothesis

What system boundary, ownership rule, failure model, or coordination idea does
this change explore?

## Origin and lifecycle

- Originating Discussion or Issue:
- Experiment dossier:
- Current stage: `proposed`, `experiment`, `decision-needed`, `concluded`, or
  `archived`
- Proposed transition, if any:

A merge records reviewed source changes. It does not conclude or promote the
experiment automatically.

## Experiment and evidence

What executable sketch, fixture, test, trace, or review result makes the idea
inspectable? List commands that were actually run and checks that were skipped.

## Unproven and residual risk

What does the experiment not establish? Include assumptions, unsafe uses,
provider or platform gaps, and ways the idea could be superseded or removed.

## Repository effects

- [ ] User-visible changes are recorded under `Unreleased` in `CHANGELOG.md`.
- [ ] `STATUS.md`, affected READMEs, schemas, examples, and CLI help remain
      consistent with the source-only incubator boundary.
- [ ] No registry publishing, release automation, compatibility promise, or
      supported-version promise is introduced.
- [ ] New network, model, filesystem, credential, or mutation surfaces are
      called out for human review.
- [ ] The experiment dossier records non-guarantees, success and refusal cases,
      observations, and the proposed next transition.
- [ ] A maintainer, not an agent or passing check, explicitly owns any
      `concluded` or `archived` transition.
