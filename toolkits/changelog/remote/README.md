# ph-changelog-remote

`ph-changelog-remote` is the network-bound adapter for the deterministic
`ph-changelog` package. It retrieves one raw changelog over a constrained
HTTP request and emits the same versioned, lossless machine document as the
core `inspect` command. The shared fields and compatibility rules are defined
in the [machine-document contract](../MACHINE_FORMAT.md).

The command permits HTTPS by default. Plain HTTP requires an explicit
`--allow-http`; it follows at most five validated redirects, and HTTPS can
never downgrade to HTTP. All hops share one deadline, and redirect bodies are
closed without being downloaded. Authentication, proxy configuration, custom
headers, disabled TLS verification, compressed responses, HTML, and non-UTF-8
content are intentionally unsupported. Generic raw-file hosts may serve
Markdown as
`application/markdown` or `application/octet-stream`; those media types remain
subject to the same strict UTF-8, size, and changelog validation checks.
Only complete `200` snapshots are accepted; partial-range responses,
premature EOF, and ambiguous length or transfer framing are operational
failures.

```bash
uv run --locked ph-changelog-remote fetch \
  https://raw.githubusercontent.com/OWNER/REPOSITORY/main/CHANGELOG.md \
  --output changelog.json
uv run --locked ph-changelog-remote --profile ph-eventing fetch \
  https://raw.githubusercontent.com/OWNER/REPOSITORY/main/CHANGELOG.md \
  --max-bytes 1048576
```

Supply a raw-file URL, not a repository HTML page. The defaults are a
10-second overall retrieval deadline and a 4 MiB response limit.
`PH_CHANGELOG_PROFILE` changes the default profile, and command-line options
take precedence.

The JSON is written to stdout when `--output` is omitted or is `-`. A file
output is replaced atomically only after retrieval and deconstruction succeed.
Exit status `0` means the fetched changelog is valid for the selected profile,
`1` means JSON was emitted but validation found issues, and `2` means an
operational failure occurred and no output file was replaced.

Query strings are sent when supplied, but are removed from source metadata and
error messages. Do not use this command for authenticated or secret-bearing
URLs. The adapter is not a network sandbox; apply host-level egress policy when
URLs do not come directly from a trusted operator.
