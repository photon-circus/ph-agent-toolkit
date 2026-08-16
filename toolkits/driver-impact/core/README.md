# ph-driver-impact

`ph-driver-impact` is a deterministic, offline, read-only inspector for changes
to contract-first driver repositories. It compares two local Git states,
classifies changed surfaces with an explicit profile, indexes repository-owned
contracts, and emits versioned impact obligations. It does not decide whether a
change is correct and does not run the suggested validation commands.

## Inspect a worktree

```bash
uv run --locked ph-driver-impact inspect \
  --repo ../ph-ads1115-adc \
  --base HEAD \
  --target worktree \
  --profile photon-circus-driver-v1 \
  --output impact.json
```

Exit status `0` means no changed surface was found. Exit status `3` means a
valid report was produced and review is required. Exit status `2` is a refusal
or operational error.

`--target` may instead name another locally available commit. The core never
fetches a revision. Worktree inspection includes tracked, staged, unstaged, and
untracked files, records hashes for every consumed file, and refuses if a
consumed file changes during inspection.

Use `--format summary` for a short human rendering. JSON is the canonical
machine contract. An output path inside the inspected repository is excluded
from untracked-file discovery so an earlier report does not inspect itself.

## Interpretation

Obligation strengths are deliberately distinct:

- `required` comes from a deterministic profile rule;
- `candidate` identifies a likely coupled edit;
- `supervisor_decision` marks authority the inspector cannot exercise; and
- `informational` provides context only.

`clear` means that no profile obligation was found. It never means that the
implementation is correct. Unknown paths remain visible through
`unclassified`; binary changes retain their paths and hashes but no text patch.

The built-in `photon-circus-driver-v1` profile indexes existing Markdown by
document, heading ancestry, table row, and content hash. Stable numeric IDs are
not required, so current Photon Circus driver repositories can adopt the tool
without first rewriting their contracts.

## Refusal boundaries

The core refuses unresolved merge conflicts, missing revisions, invalid
profiles, configured size-limit violations, missing required authority files,
non-local comparisons, and stale consumed worktree bytes. It never reads vendor
PDF contents, interprets HIL evidence, promotes capability tiers, mutates the
repository, runs checks, or contacts a model or network service.
