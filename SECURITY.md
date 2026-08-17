# Security Policy

> [!WARNING]
> This repository is a living, source-only incubator—not a security-supported
> product or trust boundary. See [STATUS.md](STATUS.md).

## Supported versions

No version is security-supported, and no release line is planned. The `main`
branch may receive best-effort fixes without an SLA, backport, disclosure, or
compatibility commitment.

## Reporting a vulnerability

Report vulnerabilities privately to `steve@giacomelli.ca`. Do not open a
public issue for a vulnerability involving unsafe file mutation, command
injection, secret disclosure, path traversal, untrusted model output, or a
way to treat modified release history as validated. This also includes an
outbound-request bypass or URL credential disclosure in the remote adapter.

Include the affected revision, reproduction steps, impact, and any suggested
mitigation. We aim to acknowledge reports when capacity allows, but there is no
response-time or remediation SLA. Please allow time for a coordinated fix
before public disclosure.

The toolkit does not make a model provider trustworthy. Callers remain
responsible for endpoint access controls and for excluding secrets from agent
facts and prompts.

`ph-changelog-remote` makes an outbound request only when its `fetch` command
is invoked. Accept only URLs selected and reviewed by the operator, and treat
fetched content as untrusted. Do not let model output choose URLs without
supervisor validation. The adapter applies current response-size and protocol
checks, but it is not an SSRF defense, network sandbox, or substitute for
host-level egress controls. URL query strings are removed from emitted
provenance and diagnostics to reduce accidental credential disclosure.
