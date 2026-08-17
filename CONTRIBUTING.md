# Contributing

> [!NOTE]
> Contributions refine a living concept incubator, not a product or release
> line. Interfaces and experiments may be replaced or removed. Read
> [STATUS.md](STATUS.md) before proposing a change.

Read [AGENTS.md](AGENTS.md), [the architecture](docs/ARCHITECTURE.md), and the
affected toolkit README before making a change.

## Development setup

Install uv, clone the repository, and run:

```bash
uv sync --all-packages --locked
```

Keep changes focused. Add or update tests for every behavior change, and keep
deterministic core code independent from agent assets and providers.

## Required checks

```bash
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked python -m unittest discover -s toolkits/changelog/core/tests -v
uv run --locked python -m unittest discover -s toolkits/changelog/agent/tests -v
uv run --locked python -m unittest discover -s toolkits/changelog/remote/tests -v
```

A pull request should explain which boundary hypothesis changed, what evidence
supports it, what was tested, and what remains unproven. Passing the required
checks is regression evidence only, not production assurance. Update
`[Unreleased]` in `CHANGELOG.md` for visible changes.

Do not add unvalidated model output paths, weaken released-history protection,
commit secrets, or introduce a runtime dependency without documenting why the
standard library is insufficient.

Do not add publishing automation, registry credentials, or language that
describes this repository as stable, supported, hardened, safe, trusted,
production-ready, or on a path to release.

By contributing, you agree that your contribution is licensed under the MIT
License and that participation follows the [Code of Conduct](CODE_OF_CONDUCT.md).
