# Incubator status

> [!WARNING]
> **Living experiment. Source-only concept incubator. Not a trusted implementation.**
> This repository intentionally collects concepts, boundary hypotheses,
> sketches, executable experiments, and potential code for layered agent
> systems. It is not a product, a supported package set, a production
> implementation, or a release candidate.

## Intent

This repository exists to make ideas inspectable and testable while they are
still changing. In particular, it explores systemic boundaries between model
judgment, deterministic operations, transport, file mutation, and human
supervision.

Executable code is present so that an idea can be exercised against examples
and tests. Executability is not a maturity claim. A component may be
incomplete, illustrative, superseded, abandoned, moved to a separately owned
project, or removed entirely.

The repository is not intended to graduate into a published distribution:

- no package here is intended for upload to a package registry;
- version fields are internal workspace coordinates, not release promises;
- there are no supported versions, release lines, backports, or migration
  commitments;
- APIs, schemas, commands, defaults, and package boundaries may change or
  disappear without notice;
- there is no production-readiness, security-review, compatibility, or
  response-time SLA.

An idea that matures should move to a separately named repository and establish
its own support, compatibility, security, and release contracts. Maturity in an
extracted project does not change the status of this incubator.

## Appropriate use

- reading and discussing architecture experiments;
- reproducing a narrowly described behavior;
- supervised trials in disposable or version-controlled working copies;
- comparing boundary hypotheses before adopting an idea elsewhere.

## Inappropriate use

- production, release, or security-critical automation;
- unattended agents or irreversible workflows;
- use as a security, trust, authorization, or isolation boundary;
- processing secrets or sensitive repository content;
- depending on package names, APIs, schemas, or output formats as stable;
- treating a green test run, a successful parse, or exit status `0` as an
  assurance statement.

## How to read project claims

| Term | Narrow meaning in this repository | What it does not mean |
| --- | --- | --- |
| deterministic | The described path excludes model or network interaction and is intended to repeat for the same inputs and environment. | Correct, secure, race-free, portable, or proven. |
| bounded | The current revision contains the stated checks or limits. | Sandboxed, isolated, least-privileged, or safe for hostile input. |
| contract-checked | Data passed the current shape, type, section-authority, and reference checks. | Factually true, semantically entailed, prompt-injection resistant, or trustworthy. |
| atomic replacement | One current write path attempts a same-directory filesystem replacement after its documented checks. | A durable transaction, backup, multi-file commit, symlink defense, permission preservation, or freedom from all races. |
| lossless | Accepted UTF-8 input bytes are retained in the current machine-document field. | A general archival or recovery guarantee. |
| protected history | Current parser/profile checks refuse some changes to parsed released history. | Tamper-proofing, authenticity, or complete release-policy enforcement. |
| tested | The checked cases passed in the environments that actually ran. | Exhaustive verification, independent audit, or fitness for another environment. |

## Known trust gaps

This list is intentionally direct and non-exhaustive:

- The agent path sends supervisor facts, selected skill material, and current
  changelog prose to the configured model endpoint. A loopback default does not
  make a provider or its output trusted, and endpoint overrides may disclose
  that content.
- Agent-output checks constrain structure and references; they do not prove
  that prose follows from cited facts. Literal forbidden-claim checks are not a
  semantic verifier.
- Agent application checks the target changelog snapshot, not the repository
  revision or the freshness of evidence behind supervisor facts.
- File-mutation paths are experiments, not a filesystem sandbox or transaction
  system. Some paths have narrower replacement and stale-write checks than
  others.
- The remote adapter applies explicit protocol and size checks, but it is not
  an SSRF defense or network sandbox. Operator-selected URLs may still reach
  addresses allowed by the host network.
- Custom profiles, skill overrides, and integration templates are
  consumer-controlled inputs. They can change or weaken policy and are not an
  assurance boundary.

## If you run an experiment

Pin the exact commit, use a clean disposable branch, keep recoverable backups,
exclude secrets, prefer a loopback model endpoint, constrain network egress,
inspect generated proposals, and review every diff before accepting a change.

Only an explicit owner decision may change this status document. Repository
age, code volume, test count, or apparent completeness must not be interpreted
as an implicit change in maturity.
