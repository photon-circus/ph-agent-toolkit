# Changelog toolkit

The changelog toolkit treats `CHANGELOG.md` as a protected structured artifact
while keeping prose generation bounded and optional.

## Packages

| Package | Command | Responsibility |
| --- | --- | --- |
| `core/` (`ph-changelog`) | `ph-changelog` | Offline parsing, validation, normalization, insertion, and semantic merge |
| `agent/` (`ph-changelog-agent`) | `ph-changelog-agent` | Fact/output contracts, prompt assembly, provider calls, and validated application |
| `remote/` (`ph-changelog-remote`) | `ph-changelog-remote` | Bounded HTTP(S) retrieval and machine-document output |

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

## Agent authority boundary

The supervisor supplies structured facts and authorizes target sections. The
model returns prose plus the fact IDs supporting it. Deterministic code then:

1. validates the facts and output contract;
2. refuses unauthorized sections, unknown fact citations, and explicitly
   forbidden literal claims;
3. inserts entries without allowing the model to place Markdown;
4. revalidates the complete changelog;
5. checks for intervening file changes immediately before atomic replacement.

The model never edits release headings or released history directly.
`allowed_claims` guides the bounded prose model; deterministic validation cannot
prove that arbitrary prose is semantically supported by a cited fact.

## Consumer integrations

The files under `integrations/` are templates for a downstream repository that
has added `ph-changelog` to its own locked uv project. Review branch names and
choose the correct profile before adopting them.
