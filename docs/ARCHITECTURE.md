# Architecture

> [!WARNING]
> This document records current design hypotheses inside a living incubator.
> It is not an assurance case, independent audit, verified security
> architecture, or production design. "Must" describes repository intent;
> tests establish only the cases they cover. See [STATUS.md](../STATUS.md).

## Purpose

`ph-agent-toolkit` explores repeatable task workflows intended to constrain
model authority over a repository. Each experiment is split at the point where
deterministic evidence currently ends and model judgment begins.

## Toolkit layers

```text
supervisor facts
      |
      v
agent contract + prompt + provider   (optional, nondeterministic)
      |
      v
schema/contract-checked proposal
      |
      v
offline transformation core         (owns current mutation sketches)
      |
      v
repository artifact
```

A core package may contain parsers, policy checks, normalizers, merge
algorithms, profiles, serialization, and CLI mutation experiments. The
dependency rule is that it remains usable without installing or importing its
agent peer; this rule is not a claim of filesystem safety.

An agent package may contain task-fact/output contracts, prompt construction,
skills, examples, and provider adapters. It depends on the core for every
artifact mutation and runs the current shape and authority checks on model
output before application. Those checks do not establish semantic truth.

A transport adapter may retrieve an artifact from an external system, enforce
protocol and size limits, and pass the exact bytes to the core. It depends on
the core; neither the core nor an agent package may depend on the adapter.

Integration templates show consumers how to call current experimental command
surfaces. They are examples, not active policy, supported deployment
configuration, or release controls for this repository.

## Changelog capability

`ph-changelog` owns Markdown parsing, profile checks, current insertion and
normalization rules, released-history refusal checks, a narrow additive merge
experiment, and the machine-document serializer. It does not import model or
HTTP code.

`ph-changelog-remote` owns HTTP(S) retrieval with the current protocol,
redirect, deadline, and body-size checks; remote provenance; and a
same-directory JSON replacement path. It passes fetched bytes to
`ph-changelog` and contains no model interaction. It is not an SSRF defense or
network sandbox.

`ph-changelog-agent` owns supervisor-fact checks, model-output contract checks,
prompt assembly, the LM Studio-compatible provider, and a changelog snapshot
comparison followed by same-directory replacement.
It may call only the public deterministic operations from `ph-changelog`.

These responsibility assignments limit dependency direction; they do not make
the model, provider, supplied facts, profile, skill override, filesystem, or
network trustworthy. The exact residual limitations are recorded in
[STATUS.md](../STATUS.md).

```text
ph-changelog-agent   --->  ph-changelog  <---  ph-changelog-remote
       model I/O           offline core          HTTP(S) I/O
```

## Adding a capability

Add `toolkits/<capability>/core` first. Define its input/output and refusal
tests before adding `agent`. If no model judgment is necessary, omit the agent
package. Each distributable package joins the root uv workspace and exposes a
capability-specific console command.
