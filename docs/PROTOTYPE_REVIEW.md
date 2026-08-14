# `ph-doc-prototype` review and migration

## Baseline reviewed

The prototype contained a dependency-free Python changelog parser, validator,
normalizer, structured insertion tool, semantic three-way merge, supervisor
fact contract, bounded LM Studio prose worker, profiles, schemas, examples,
and integration templates. Its 18 characterization tests passed on Python
3.14.7 before migration.

It was not uv-managed in operation: `[tool.uv] package = false` was paired with
no lockfile or console entry point, and its README, shell scripts, GitHub
template, and merge driver invoked bare `python` through a launcher that
manually changed `sys.path`.

## Findings

- Deterministic and model-facing code shared one `ph_doc` package and CLI; the
  deterministic command imported the network-capable agent module eagerly.
- Default profile and skill paths depended on the caller's working directory.
- Text-mode file I/O weakened the byte-preservation claim on Windows.
- Semantic merge could discard changed preamble text and did not fail closed
  on duplicate subsections.
- Validation did not reject duplicate normalized entries.
- Handwritten agent validators did not fully enforce their JSON schemas.
- A long model call could overwrite a changelog changed by another process
  before `--apply` completed.
- The sample GitHub workflow was inactive here, targeted `master`, and neither
  installed uv nor ran the test suite.

## Migration decisions

The prototype name is retired in favor of `toolkits/changelog`. Its code is
split into the independently installable `ph-changelog` core and
`ph-changelog-agent` package. The root is a locked uv workspace, and all
documented Python execution goes through `uv run --locked`.

The migration also packages built-in profiles and agent resources, uses
byte-preserving UTF-8 file I/O, supports both bracketed and unbracketed Keep a
Changelog headings, rejects unsafe merge inputs and duplicate entries, aligns
agent validation with its schemas, and makes agent application snapshot-checked
and atomic.

## Deliberate remaining scope

The release comparator remains intentionally limited to the prototype's simple
SemVer triplet ordering. Prerelease precedence is not a supported ordering
contract yet. The first agent provider remains a local LM Studio-compatible
endpoint; adding providers must not change the core boundary.

The integration files are templates. Adopting them in another repository
still requires selecting a profile and matching that repository's branch and
release policy.
