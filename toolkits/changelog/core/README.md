# ph-changelog

> [!WARNING]
> **Incubator-only source.** This directory resembles an installable package so
> experiments can be exercised, but it is not a supported distribution and is
> not intended for publication. See the repository
> [STATUS.md](../../../STATUS.md).

`ph-changelog` is the experimental offline half of the Photon Circus
changelog toolkit. It checks a narrow Keep a Changelog grammar, inserts and
normalizes `Unreleased` entries, applies current released-history refusal
checks, and attempts a narrow additive merge. It also deconstructs accepted
UTF-8 snapshots into the current versioned JSON experiment.

It has no runtime dependencies and no agent or network imports.

Offline and repeatable do not mean correct or safe. Mutation commands operate
on files, and their checks are not a filesystem sandbox, transaction, backup,
or complete defense against symlinks and concurrent writers. Use a disposable
version-controlled copy and inspect every diff.

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
default. Its accepted-UTF-8 byte snapshot, semantic releases/sections/entries, source
metadata, and validation issues follow the shared
[machine-document contract](../MACHINE_FORMAT.md). Exit `0` means the document
passed the current parser and selected-profile checks, `1` means JSON was
emitted with reported issues, and `2` means an operational error prevented
output. None of those statuses is an assurance result.

`add --input operation.json` accepts either one closed operation object or an
`{"entries": [...]}` wrapper. Each operation requires non-empty string
`section` and `entry` fields and may include a boolean `breaking` field;
unknown fields and mistyped values are rejected before mutation.

The built-in profiles are `photon-circus` and `ph-eventing`. `--profile` also
accepts a JSON file. `PH_CHANGELOG_PROFILE` changes the default profile.
Profiles are policy inputs, not trust anchors; a custom profile may weaken the
checks while choosing any display name.

`check --base` compares the released-history slice after UTF-8 decoding
without platform newline translation. Mutation commands write encoded bytes
directly, so matching historical slices retain their original line endings.

The parser accepts `## Unreleased` and `## [Unreleased]`, with matching plain
or bracketed `X.Y.Z - YYYY-MM-DD` release headings. Prerelease precedence is
outside the current ordering contract.
