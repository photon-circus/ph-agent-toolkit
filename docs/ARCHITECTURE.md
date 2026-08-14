# Architecture

## Purpose

`ph-agent-toolkit` packages repeatable task workflows without giving a model
unbounded authority over a repository. Every capability is split at the point
where deterministic evidence ends and model judgment begins.

## Toolkit layers

```text
supervisor facts
      |
      v
agent contract + prompt + provider   (optional, nondeterministic)
      |
      v
validated structured proposal
      |
      v
deterministic core                   (offline, owns mutations)
      |
      v
repository artifact
```

A core package may contain parsers, validators, normalizers, merge algorithms,
profiles, serialization, and file-safe CLI operations. It must remain usable
without installing or importing its agent peer.

An agent package may contain task-fact/output contracts, prompt construction,
skills, examples, and provider adapters. It depends on the core for every
artifact mutation and validates model output before application.

A transport adapter may retrieve an artifact from an external system, enforce
protocol and size limits, and pass the exact bytes to the core. It depends on
the core; neither the core nor an agent package may depend on the adapter.

Integration templates show consumers how to call stable console commands.
They are examples, not active policy for this repository.

## Changelog capability

`ph-changelog` owns Markdown parsing, profile validation, canonical insertion,
normalization, released-history protection, conservative semantic merge, and
the versioned machine-document serializer. It does not import model or HTTP
code.

`ph-changelog-remote` owns bounded HTTP(S) retrieval, remote provenance, and
atomic JSON output. It passes fetched bytes to `ph-changelog` and contains no
model interaction.

`ph-changelog-agent` owns supervisor-fact validation, model-output validation,
prompt assembly, the LM Studio-compatible provider, and snapshot-checked atomic
application.
It may call only the public deterministic operations from `ph-changelog`.

```text
ph-changelog-agent   --->  ph-changelog  <---  ph-changelog-remote
       model I/O           offline core          HTTP(S) I/O
```

## Adding a capability

Add `toolkits/<capability>/core` first. Define its input/output and refusal
tests before adding `agent`. If no model judgment is necessary, omit the agent
package. Each distributable package joins the root uv workspace and exposes a
capability-specific console command.
