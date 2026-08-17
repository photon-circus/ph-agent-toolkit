# Changelog

This records notable changes to a living, source-only incubator. There are no
supported release lines, published distributions, or compatibility
commitments. The layout follows Keep a Changelog and version labels use
Semantic Versioning syntax; neither is a maturity, stability, or
production-readiness claim.

## [Unreleased]

### Added

- Document the repository as a living concept incubator that is not intended
  for package publication, production use, or use as a trust boundary.
- Add a discussion-to-experiment workflow, structured contribution forms,
  lifecycle guidance, experiment dossiers, and provisional decision records.
- Establish the Photon Circus root documentation set and canonical agent
  operating guide.
- Add a uv-managed workspace for reusable task toolkits.
- Introduce the changelog toolkit with separate `ph-changelog` deterministic
  core and `ph-changelog-agent` agent packages.
- Add a closed, versioned machine-readable changelog document with lossless
  source bytes, semantic releases and entries, and profile validation issues.
- Add offline `ph-changelog inspect` and a separate bounded
  `ph-changelog-remote fetch` adapter for local and remote snapshots.

### Changed

- Replace the `ph-doc-prototype` name and source-path launcher with installed
  console commands and an explicit `agent -> core` dependency boundary.
