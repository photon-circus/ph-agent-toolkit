# Experimental Decision Records

Experimental Decision Records (EDRs) capture working design choices made while
exploring `ph-agent-toolkit`.

An EDR is not an assurance claim, security approval, compatibility promise, or
production architecture decision. Its assurance remains **experimental** even
when its state is `current`.

## When to write an EDR

Write an EDR when an experiment reaches `decision-needed` because it exposes a
choice that affects:

- authority between layers;
- validation or refusal behavior;
- mutation ownership;
- provider or transport boundaries;
- proposal, evidence, or lifecycle contracts.

Routine implementation details do not need an EDR unless they change one of
those boundaries.

## Naming

Use:

    EDR-NNNN-short-title.md

Numbers are repository-local and monotonically increasing.

Start from [`EDR_TEMPLATE.md`](EDR_TEMPLATE.md).

## Record states

- `draft`: under discussion;
- `current`: the working choice for continued experiments;
- `superseded`: replaced by a later EDR;
- `reversed`: deliberately abandoned after new evidence or constraints.

These states describe repository guidance, not implementation maturity.

Once an EDR is `current`, preserve its reasoning. Make only corrective edits
for wording or links; record substantive changes in a new EDR that supersedes
or reverses it.

## Evidence discipline

Link the experiments, cases, observations, and evidence records considered.
Clearly separate:

- observations from interpretations;
- deterministic checks from semantic judgment;
- chosen tradeoffs from properties not established.

Model output may inform an experiment, but it cannot approve an EDR.
