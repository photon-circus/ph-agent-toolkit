# AGENTS.md — `ph-agent-toolkit`

**Canonical operating instructions for humans and coding agents.**
`CLAUDE.md` points here; do not duplicate these rules elsewhere.

## What this is

A living, source-only concept incubator for agent-assisted work across Photon
Circus repositories. It is not a product, supported distribution, trusted
implementation, or release candidate. A toolkit combines an experimental
offline core with optional transport and agent layers. The first experiment
manages changelogs.

## Canonical sources

| Subject | Canonical source |
| --- | --- |
| Incubator status and trust vocabulary | `STATUS.md` |
| Cross-toolkit boundaries | `docs/ARCHITECTURE.md` |
| Prototype findings and migration decisions | `docs/PROTOTYPE_REVIEW.md` |
| User-facing setup and commands | `README.md` |
| Released and pending changes | `CHANGELOG.md` |
| Python dependencies | `pyproject.toml` and `uv.lock` |
| Changelog core behavior | `toolkits/changelog/core/README.md` and tests |
| Changelog machine format | `toolkits/changelog/MACHINE_FORMAT.md` and packaged schema |
| Remote retrieval behavior | `toolkits/changelog/remote/README.md` and tests |
| Changelog agent contract | `toolkits/changelog/agent/README.md`, schemas, and tests |

When documents disagree, correct the non-owning document in the same change.

## Required reading

1. `STATUS.md`
2. `docs/ARCHITECTURE.md`
3. The affected toolkit's README files
4. `docs/PROTOTYPE_REVIEW.md` when changing the changelog toolkit
5. The affected tests and schemas

## Public claim discipline

- Always describe this repository as a living, source-only incubator.
- Never describe it as production-ready, stable, supported, trusted, secure,
  safe, hardened, audited, battle-tested, or on a path to package publication.
- Scope every use of deterministic, bounded, contract-checked, atomic,
  lossless, protected, or tested to the exact mechanism and residual
  limitation. Follow the vocabulary in `STATUS.md`.
- "Adopted" and "canonical" mean organizational ownership inside the current
  experiment; they are not maturity labels.
- Green CI is regression evidence, not a security review or readiness signal.
- Removing `prototype` from a directory name does not mean the concept is
  mature.

## Hard boundaries

- Core packages are deterministic and offline. They may not import an agent
  package, prompt asset, model SDK, or network client.
- Remote adapters may depend on core packages and perform only explicit,
  bounded transport. Core and agent packages may not depend on them.
- Agent packages may depend on their core package and must communicate through
  explicit, validated data contracts.
- Models propose bounded structured data. Deterministic code validates and
  applies every mutation.
- Released changelog history is immutable in ordinary changes.
- Do not weaken a validator, schema, or regression test merely to accept model
  output.
- Changes made by users or other agents are valid; never discard unrelated
  work.

## Repository layout

```text
docs/                     cross-toolkit contracts and decisions
toolkits/<capability>/
  core/                   deterministic distribution
  remote/                 optional bounded transport adapter
  agent/                  agent contract, assets, and providers
  examples/               end-to-end structured examples
  integrations/           downstream templates, not active repo policy
```

Python distribution names use kebab-case (`ph-changelog`); import packages
use snake_case (`ph_changelog`). Capability directories use lowercase
kebab-case and must not include `prototype` once adopted.

## Commands

```bash
uv sync --all-packages --locked
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked python -m unittest discover -s toolkits/changelog/core/tests -v
uv run --locked python -m unittest discover -s toolkits/changelog/agent/tests -v
uv run --locked python -m unittest discover -s toolkits/changelog/remote/tests -v
uv run --locked ph-changelog --help
uv run --locked ph-changelog-agent --help
uv run --locked ph-changelog-remote --help
```

Use uv for every Python command in documentation, scripts, and automation. Do
not restore source-path launchers or bare `python` entry points.

## Workflow

1. Identify whether the change belongs to core, remote transport, agent, or
   integration assets.
2. Update the owning contract or schema before changing behavior.
3. Add the smallest regression test that protects the boundary.
4. Implement without reversing the `agent -> core` dependency direction.
5. Run all package suites and Ruff from the workspace root.
6. Update README examples and `CHANGELOG.md` when the public workflow changes.

## Coupled edits

| If this changes | Also inspect |
| --- | --- |
| Console command or option | Root/toolkit READMEs, integrations, CLI tests |
| Machine document contract | packaged schema, core/remote tests, both READMEs |
| Remote retrieval policy | remote tests, `SECURITY.md`, architecture |
| Agent input/output contract | JSON schemas, examples, prompt, contract tests |
| Built-in profile or heading grammar | parser, validator, operations, merge tests |
| Packaged resource path | installed-resource tests and CLI defaults |
| Workspace dependency | member pyprojects, root sources, `uv.lock` |

## Definition of done

- [ ] Core remains offline and independent of the agent distribution.
- [ ] Remote transport remains explicit, bounded, and isolated from core and
      agent packages.
- [ ] Structured inputs fail closed on missing, unknown, or mistyped fields.
- [ ] File mutations preserve protected history and check for stale agent reads
      immediately before replacement.
- [ ] Tests cover the changed success and refusal paths.
- [ ] `uv.lock` matches every dependency change.
- [ ] Ruff format/lint checks and all test suites pass.
- [ ] Public behavior is recorded under `CHANGELOG.md` → `[Unreleased]`.
- [ ] Public wording still identifies the work as an incubator and does not
      overstate trust, safety, support, or publication intent.

## Dependencies and publishing

Prefer the standard library. A runtime dependency needs a concrete contract or
maintenance benefit and must stay in the narrowest package. Lock all changes
with uv.

All packages are source-only experiments and must retain the
`Private :: Do Not Upload` classifier. Agents may build and test distributions
locally but must not upload packages, create releases or tags, add publishing
automation, or publish to a registry. A concept that is ready to graduate must
move to a separately named repository through an explicit owner decision.
