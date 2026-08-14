# Security Policy

## Supported versions

The unreleased `main` branch receives best-effort security fixes. Supported
release lines will be listed here after the first release.

## Reporting a vulnerability

Report vulnerabilities privately to `steve@giacomelli.ca`. Do not open a
public issue for a vulnerability involving unsafe file mutation, command
injection, secret disclosure, path traversal, untrusted model output, or a
way to treat modified release history as validated. This also includes an
outbound-request bypass or URL credential disclosure in the remote adapter.

Include the affected revision, reproduction steps, impact, and any suggested
mitigation. You should receive acknowledgement within 72 hours. Please allow
time for a coordinated fix before public disclosure.

The toolkit does not make a model provider trustworthy. Callers remain
responsible for endpoint access controls and for excluding secrets from agent
facts and prompts.

`ph-changelog-remote` makes an outbound request only when its `fetch` command
is invoked. Treat supplied URLs as trusted operator input: do not let model
output choose them without supervisor validation. The adapter bounds response
size and protocol behavior, but it is not a network sandbox or a substitute
for host-level egress controls. URL query strings are removed from emitted
provenance and diagnostics to reduce accidental credential disclosure.
