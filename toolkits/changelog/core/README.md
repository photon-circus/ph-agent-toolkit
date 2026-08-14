# ph-changelog

`ph-changelog` is the offline, deterministic half of the Photon Circus
changelog toolkit. It validates a narrow Keep a Changelog grammar, inserts and
normalizes `Unreleased` entries, protects released history, and conservatively
merges independent additive changes. It also deconstructs exact UTF-8 snapshots
into a versioned JSON document.

It has no runtime dependencies and no agent or network imports.

## Commands

```bash
uv run --locked ph-changelog --profile photon-circus check CHANGELOG.md
uv run --locked ph-changelog --profile photon-circus inspect \
  CHANGELOG.md --output changelog.json
uv run --locked ph-changelog --profile photon-circus normalize CHANGELOG.md --write
uv run --locked ph-changelog --profile photon-circus add CHANGELOG.md \
  --section Fixed --entry "Describe the externally meaningful correction." --write
uv run --locked ph-changelog --profile photon-circus merge \
  BASE_CHANGELOG OURS_CHANGELOG THEIRS_CHANGELOG --output MERGED_CHANGELOG
```

`inspect` accepts a file path or `-` for stdin and writes JSON to stdout by
default. Its lossless artifact, semantic releases/sections/entries, source
metadata, and validation issues follow the shared
[machine-document contract](../MACHINE_FORMAT.md). Exit `0` means the document
is valid for the selected profile, `1` means JSON was emitted with validation
issues, and `2` means an operational error prevented output.

`add --input operation.json` accepts either one closed operation object or an
`{"entries": [...]}` wrapper. Each operation requires non-empty string
`section` and `entry` fields and may include a boolean `breaking` field;
unknown fields and mistyped values are rejected before mutation.

The built-in profiles are `photon-circus` and `ph-eventing`. `--profile` also
accepts a JSON file. `PH_CHANGELOG_PROFILE` changes the default profile.

`check --base` compares released history exactly after UTF-8 decoding without
platform newline translation. Mutation commands write encoded bytes directly,
so protected historical slices retain their original line endings.

The parser accepts `## Unreleased` and `## [Unreleased]`, with matching plain
or bracketed `X.Y.Z - YYYY-MM-DD` release headings. Prerelease precedence is
outside the current ordering contract.
