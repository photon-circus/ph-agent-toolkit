# AGENTS.md — `ph-agent-toolkit`

**Canonical operating instructions for humans and coding agents.**
`CLAUDE.md` points here; do not duplicate these rules elsewhere.

## What this is

A uv-managed Python workspace of reusable task toolkits for agent-assisted
work across Photon Circus repositories. A toolkit combines a deterministic
core with optional bounded transport and agent layers. The first toolkit
manages changelogs.

## Canonical sources

| Subject | Canonical source |
| --- | --- |
| Cross-toolkit boundaries | `docs/ARCHITECTURE.md` |
| Prototype findings and migration decisions | `docs/PROTOTYPE_REVIEW.md` |
| User-facing setup and commands | `README.md` |
| Released and pending changes | `CHANGELOG.md` |
| Python dependencies | `pyproject.toml` and `uv.lock` |
| Changelog core behavior | `toolkits/changelog/core/README.md` and tests |
| Changelog machine format | `toolkits/changelog/MACHINE_FORMAT.md` and packaged schema |
| Remote retrieval behavior | `toolkits/changelog/remote/README.md` and tests |
| Changelog agent contract | `toolkits/changelog/agent/README.md`, schemas, and tests |
| Driver impact behavior | `toolkits/driver-impact/core/README.md`, profile, schema, and tests |
| Driver impact agent contract | `toolkits/driver-impact/agent/README.md`, schemas, and tests |

When documents disagree, correct the non-owning document in the same change.

## Required reading

1. `docs/ARCHITECTURE.md`
2. The affected toolkit's README files
3. `docs/PROTOTYPE_REVIEW.md` when changing the changelog toolkit
4. The affected tests and schemas

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
uv run --locked python -m unittest discover -s toolkits/driver-impact/core/tests -v
uv run --locked python -m unittest discover -s toolkits/driver-impact/agent/tests -v
uv run --locked ph-changelog --help
uv run --locked ph-changelog-agent --help
uv run --locked ph-changelog-remote --help
uv run --locked ph-driver-impact --help
uv run --locked ph-driver-impact-agent --help
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
| Driver-impact profile rule | core tests, examples, both driver-impact READMEs |
| Driver-impact agent contract | agent schemas, prompt, examples, and contract tests |

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

## Dependencies and publishing

Prefer the standard library. A runtime dependency needs a concrete contract or
maintenance benefit and must stay in the narrowest package. Lock all changes
with uv.

Agents may build and test distributions locally but must not upload packages,
create releases, or publish to a registry. Publishing is an owner action.
