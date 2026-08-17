# Experiments

This directory contains source-controlled investigations into agent authority,
validation, mutation, transport, and evidence boundaries.

Every experiment is experimental. A concluded or archived experiment is not a
trusted implementation or production recommendation.

## Layout

Each experiment uses a stable lowercase identifier:

    experiments/<experiment-id>/
      README.md
      cases/
      proposals/
      evidence/
      observations/

Only `README.md` is required. Add the other directories when the experiment
produces those record types.

Start by copying [`EXPERIMENT_TEMPLATE.md`](EXPERIMENT_TEMPLATE.md).

## Record types

- `cases/` contains success, refusal, and escalation fixtures.
- `proposals/` contains curated, contract-checked proposal examples.
- `evidence/` contains scoped observations tied to revisions or artifact
  digests.
- `observations/` contains short notes about results, surprises, and
  counterexamples.

Prefer one observation per file so later findings do not rewrite earlier
context.

## Rules

1. Keep the lifecycle stage and experimental assurance visible in the
   experiment README.
2. State what deterministic checks establish and what remains semantic
   judgment.
3. Include negative and refusal cases, not only successful examples.
4. Link observations to exact commits, commands, fixtures, or digests when
   available.
5. Treat model output, remote content, custom profiles, and prompt overrides as
   untrusted inputs.
6. Do not commit secrets, authenticated URLs, private prompts, or raw
   transcripts containing repository-sensitive material.
7. A digest establishes byte identity only; an evidence record establishes an
   observation only.
8. Record working choices in an
   [Experimental Decision Record](../docs/decisions/README.md).

Lifecycle rules are defined in
[`docs/EXPERIMENT_LIFECYCLE.md`](../docs/EXPERIMENT_LIFECYCLE.md).

Raw local run output should remain outside the committed experiment record
unless it has been reviewed and sanitized.
