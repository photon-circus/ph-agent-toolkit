# ph-agent-toolkit

> [!WARNING]
> **Status: living experiment and source-only concept incubator.** This is not
> a trusted implementation, supported package set, or release candidate. Code
> may be incomplete, illustrative, superseded, or removed. Read
> [the incubator status and trust model](STATUS.md) before using anything here.

`ph-agent-toolkit` is a living collection of task-scoped experiments in
systems design for layered agents. It explores where authority, evidence,
model judgment, transport, and mutation should cross explicit boundaries
across Photon Circus repositories. Executable code exists to test those ideas,
not to claim production fitness.

The first experiment is changelog management, migrated from the former
`ph-doc-prototype`.

## Current boundary hypotheses

The implementation currently attempts to preserve these separations:

- Deterministic tools own parsing, validation, file placement, and mutation.
- Agents receive bounded facts and return structured proposals; they do not
  directly choose Markdown structure or edit released history.
- Agent packages may depend on deterministic core packages. Core packages
  must never depend on prompts, model providers, or network access.
- Explicit transport adapters may depend on a core package, but keep remote I/O
  isolated from both deterministic document logic and model-facing code.
- Task contracts, profiles, examples, and integration templates are versioned
  beside the code that consumes them.

These are design hypotheses under active revision. Terms such as
"deterministic," "bounded," and "validated" have only the narrow meanings in
[STATUS.md](STATUS.md); they are not security or maturity labels.

## Repository layout

```text
docs/                         architecture and migration decisions
experiments/                  dossiers for bounded, reproducible explorations
toolkits/changelog/core/      offline transformation experiment and tests
toolkits/changelog/agent/     ph-changelog-agent contracts/runtime and tests
toolkits/changelog/remote/    explicit HTTP(S) retrieval experiment and tests
toolkits/changelog/examples/  supervisor and agent-output examples
toolkits/changelog/integrations/ downstream Git and GitHub templates
```

The dependency direction is:

```text
ph-changelog-agent   --->  ph-changelog  <---  ph-changelog-remote
       model I/O           offline document          HTTP(S) I/O
                              operations
```

See [Architecture](docs/ARCHITECTURE.md) for the ownership rules and
[Prototype review](docs/PROTOTYPE_REVIEW.md) for the migration rationale.

## Discuss and develop ideas

Use each GitHub surface for one stage of an idea:

```text
idea or question -> Discussion -> scoped experiment Issue -> draft PR
                                                        -> decision record
```

- Start uncertain proposals, questions, experiment reports, and
  counterexamples in [Discussions](https://github.com/photon-circus/ph-agent-toolkit/discussions).
- Open an [Issue](https://github.com/photon-circus/ph-agent-toolkit/issues)
  only when there is a reproducible defect or a bounded next experiment.
- Use a draft pull request for code, fixtures, or evidence that implements the
  scoped experiment.
- Record provisional conclusions that will guide later work under
  [`docs/decisions/`](docs/decisions/README.md).

The lifecycle is defined in
[`docs/EXPERIMENT_LIFECYCLE.md`](docs/EXPERIMENT_LIFECYCLE.md). Moving an item
through that lifecycle never changes this repository's experimental assurance
status.

## Experimental use only

Nothing in this workspace is intended for a package registry or supported
distribution. If you run an experiment, pin the repository revision, use a
disposable version-controlled checkout, exclude secrets, and inspect every
result and file diff. Do not place these commands in an unattended or
release-critical workflow.

## Quick start

Install [uv](https://docs.astral.sh/uv/), then synchronize every workspace
package from the committed lockfile:

```bash
uv sync --all-packages --locked
```

Validate a changelog with a bundled profile:

```bash
uv run --locked ph-changelog --profile ph-eventing check CHANGELOG.md
```

Deconstruct a local or remote changelog into the same versioned JSON contract:

```bash
uv run --locked ph-changelog inspect CHANGELOG.md --output changelog.json
uv run --locked ph-changelog-remote fetch \
  https://raw.githubusercontent.com/OWNER/REPOSITORY/main/CHANGELOG.md \
  --output changelog.json
```

Inspect the command surfaces:

```bash
uv run --locked ph-changelog --help
uv run --locked ph-changelog-agent --help
uv run --locked ph-changelog-remote --help
```

Only the agent command contacts a model provider. The initial provider is a
local LM Studio-compatible endpoint and defaults to `http://127.0.0.1:1234`.
The separate remote command makes a request only when `fetch` is explicitly
invoked; it may follow redirects that pass the current limits described in its
[README](toolkits/changelog/remote/README.md).

## Development checks

```bash
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked python -m unittest discover -s toolkits/changelog/core/tests -v
uv run --locked python -m unittest discover -s toolkits/changelog/agent/tests -v
uv run --locked python -m unittest discover -s toolkits/changelog/remote/tests -v
```

Repository operating rules are in [AGENTS.md](AGENTS.md). Contributions are
covered by [CONTRIBUTING.md](CONTRIBUTING.md), the
[Code of Conduct](CODE_OF_CONDUCT.md), and the [Security policy](SECURITY.md).

## License

Licensed under the [MIT License](LICENSE).
