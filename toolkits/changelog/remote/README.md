# ph-changelog-remote

> [!WARNING]
> **Incubator-only network experiment.** This adapter is not an SSRF defense,
> network sandbox, trust boundary, or supported distribution, and it is not
> intended for publication. Use only operator-reviewed URLs with host-level
> egress controls. See the repository [STATUS.md](../../../STATUS.md).

`ph-changelog-remote` is an experimental network-bound adapter for the offline
`ph-changelog` package. It retrieves one raw changelog over a constrained
HTTP request and emits the same experimental exact-snapshot machine document
as the core `inspect` command. The current shared fields are described in the
[machine-document contract](../MACHINE_FORMAT.md); they carry no compatibility
promise.

The command permits HTTPS by default. Plain HTTP requires an explicit
`--allow-http`; it follows at most five redirects that pass the current URL
checks, and HTTPS can
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
output is written through a temporary sibling and operating-system replacement
only after retrieval and deconstruction succeed. This is not a durable
transaction. Exit status `0` means the fetched changelog passed the current
parser and selected-profile checks, `1` means JSON was emitted with reported
issues, and `2` means an operational failure occurred and no output file was
replaced. None of those statuses is an assurance result.

Query strings are sent when supplied, but are removed from source metadata and
error messages. Do not use this command for authenticated or secret-bearing
URLs. Accept only URLs selected and reviewed by the operator, treat retrieved
bytes as untrusted, and apply host-level egress policy. The current checks do
not prevent access to every private, loopback, link-local, or otherwise
sensitive address available from the host.
