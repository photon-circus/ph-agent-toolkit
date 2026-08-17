# Changelog machine document

> [!WARNING]
> **Experimental schema, not a compatibility or trust contract.** See the
> repository [STATUS.md](../../STATUS.md).

The changelog toolkit emits a closed JSON contract named
`ph-changelog-document`. `schema_version` currently disciplines changes within
this incubator. It is not a public compatibility promise, and the schema may be
reset or replaced without migration before an idea moves elsewhere.

The currently packaged schema is
[`changelog_document.schema.json`](core/src/ph_changelog/schemas/changelog_document.schema.json).

## Produce a document

```bash
uv run --locked ph-changelog inspect CHANGELOG.md --output changelog.json
uv run --locked ph-changelog inspect - < CHANGELOG.md
uv run --locked ph-changelog-remote fetch \
  https://raw.githubusercontent.com/OWNER/REPOSITORY/main/CHANGELOG.md \
  --output changelog.json
```

Both commands emit only JSON on stdout. For file output, the current
implementation writes a temporary sibling and attempts an operating-system
replacement after retrieval, UTF-8 decoding, and serialization succeed. This
is not a durable transaction or general filesystem-safety guarantee.

## Contract

- `source` records a closed file, stdin, or sanitized HTTP provenance object.
- `artifact` retains the accepted UTF-8 snapshot: encoding, BOM state, byte length,
  SHA-256 digest, and exact `raw_text`. Encoding `raw_text` as UTF-8 reproduces
  the fetched or inspected bytes.
- `document` is the semantic view. It contains ordered releases and sections,
  raw subsection bodies, parsed bullet blocks, and bullet-marker-free entry
  text. It is `null` when no release tree can be parsed.
- `validation` records the selected profile, current policy-conformance result,
  and machine-readable issue objects
  with `code`, `message`, `line`, and `severity`.

The parser's internal invalid-version sentinel is never exposed. Invalid
release headings use `kind: "invalid"` with a null version and appear alongside
their validation issue.

## Exit status

- `0`: JSON was emitted and the changelog conforms to the current parser and
  selected profile. This is not a truth, authenticity, or trust result.
- `1`: JSON was emitted, but parsing or profile validation found issues.
- `2`: an operational or configuration error prevented output.

Remote URL query strings are omitted from `source` metadata. The artifact has
no retrieval timestamp, so identical response bytes and provenance serialize
deterministically.
