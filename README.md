# ph-agent-toolkit

`ph-agent-toolkit` is a collection of reusable, task-scoped building blocks
for agent-assisted development across Photon Circus repositories. Each
toolkit keeps deterministic inspection and mutation code separate from model
prompts, contracts, and providers.

The repository is in early development. It currently provides changelog
management and read-only driver change-impact inspection.

## Design boundaries

- Deterministic tools own parsing, validation, file placement, and mutation.
- Agents receive bounded facts and return structured proposals; they do not
  directly choose Markdown structure or edit released history.
- Agent packages may depend on deterministic core packages. Core packages
  must never depend on prompts, model providers, or network access.
- Explicit transport adapters may depend on a core package, but keep remote I/O
  isolated from both deterministic document logic and model-facing code.
- Task contracts, profiles, examples, and integration templates are versioned
  beside the code that consumes them.

## Repository layout

```text
docs/                         architecture and migration decisions
toolkits/changelog/core/      ph-changelog deterministic package and tests
toolkits/changelog/agent/     ph-changelog-agent contracts/runtime and tests
toolkits/changelog/remote/    bounded HTTP(S) retrieval adapter and tests
toolkits/changelog/examples/  supervisor and agent-output examples
toolkits/changelog/integrations/ downstream Git and GitHub templates
toolkits/driver-impact/core/    ph-driver-impact deterministic inspector
toolkits/driver-impact/agent/   bounded local semantic mapper
toolkits/driver-impact/examples/ versioned input/output examples
```

The dependency direction is:

```text
ph-changelog-agent   --->  ph-changelog  <---  ph-changelog-remote
       model I/O           offline document          HTTP(S) I/O
                              operations
```

The driver-impact dependency direction is:

```text
ph-driver-impact-agent  --->  ph-driver-impact
      local model              offline/read-only
```

See [Architecture](docs/ARCHITECTURE.md) for the ownership rules and
[Prototype review](docs/PROTOTYPE_REVIEW.md) for the migration rationale.

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
uv run --locked ph-driver-impact --help
uv run --locked ph-driver-impact-agent --help
```

Inspect a local driver worktree without running checks or contacting a model:

```bash
uv run --locked ph-driver-impact inspect \
  --repo ../ph-ads1115-adc \
  --base HEAD \
  --target worktree \
  --output impact.json
```

A valid report that requires review exits `3`. The optional agent command can
map that report semantically using an LM Studio-compatible local endpoint while
retaining exact core references and supervisor-only decisions.

Only the `*-agent` commands contact a model provider. Their initial provider is
LM Studio-compatible and defaults to `http://127.0.0.1:1234`; the driver-impact
agent additionally enforces a loopback origin. The separate remote command
makes a request only when `fetch` is explicitly invoked; it may follow the
bounded redirects described in its
[README](toolkits/changelog/remote/README.md).

## Development checks

```bash
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked python -m unittest discover -s toolkits/changelog/core/tests -v
uv run --locked python -m unittest discover -s toolkits/changelog/agent/tests -v
uv run --locked python -m unittest discover -s toolkits/changelog/remote/tests -v
uv run --locked python -m unittest discover -s toolkits/driver-impact/core/tests -v
uv run --locked python -m unittest discover -s toolkits/driver-impact/agent/tests -v
```

Repository operating rules are in [AGENTS.md](AGENTS.md). Contributions are
covered by [CONTRIBUTING.md](CONTRIBUTING.md), the
[Code of Conduct](CODE_OF_CONDUCT.md), and the [Security policy](SECURITY.md).

## License

Licensed under the [MIT License](LICENSE).
