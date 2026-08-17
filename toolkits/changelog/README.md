# Changelog toolkit

> [!WARNING]
> **Incubator-only experiment.** These packages are source examples, not
> trusted or supported distributions, and are not intended for publication.
> See the repository [STATUS.md](../../STATUS.md).

The changelog toolkit experiments with representing `CHANGELOG.md` as a
structured artifact while keeping model-generated prose in a separate,
optional path.

## Packages

| Package | Command | Responsibility |
| --- | --- | --- |
| `core/` (`ph-changelog`) | `ph-changelog` | Offline parsing, policy checks, normalization, insertion, and narrow merge experiments |
| `agent/` (`ph-changelog-agent`) | `ph-changelog-agent` | Fact/output contract checks, prompt assembly, provider calls, and experimental application |
| `remote/` (`ph-changelog-remote`) | `ph-changelog-remote` | Experimental HTTP(S) retrieval with current protocol and size checks |

Both adapters depend on `ph-changelog`. The reverse dependencies are
forbidden, and the agent and remote packages do not depend on one another.

## Use from this workspace

```bash
uv sync --all-packages --locked
uv run --locked ph-changelog --profile ph-eventing check CHANGELOG.md
uv run --locked ph-changelog inspect CHANGELOG.md --output changelog.json
uv run --locked ph-changelog-remote fetch \
  https://raw.githubusercontent.com/OWNER/REPOSITORY/main/CHANGELOG.md \
  --output changelog.json
uv run --locked ph-changelog-agent --help
```

Local inspection and remote retrieval emit the same closed, versioned
[machine-document contract](MACHINE_FORMAT.md).

`photon-circus` is the generic built-in profile. `ph-eventing` preserves the
prototype's stricter release-summary and legacy-history policy. A profile may
also be supplied as a JSON file path.

The agent package includes its default skill, style guide, examples, and JSON
schemas as installed resources. Callers can override the skill directory when
testing a repository-specific style.

## Current agent authority experiment

The supervisor supplies structured facts and authorizes target sections. The
model returns a proposal plus the fact IDs it cites. The current packaged path
then attempts to:

1. validate the facts and output contract;
2. refuses unauthorized sections, unknown fact citations, and explicitly
   forbidden literal claims;
3. inserts entries without allowing the model to place Markdown;
4. revalidates the complete changelog;
5. compare the target bytes immediately before a same-directory replacement.

The packaged contract exposes no direct released-history or heading edit to
model output. That is not sandboxing or semantic verification.
`allowed_claims` guides the prose model; contract checks cannot prove that
arbitrary prose is factually true or semantically supported by a cited fact.

Treat every successful result as an untrusted proposal. Use `--apply` only in a
clean, reviewable, version-controlled copy after excluding secrets and
accepting the configured provider boundary.

## Consumer integrations

The files under `integrations/` are templates for a downstream repository that
has added `ph-changelog` to its own locked uv project. Review branch names and
choose the correct profile before adopting them.
