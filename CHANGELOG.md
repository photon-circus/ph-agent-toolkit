# Changelog

All notable changes to this project are documented here.

The format follows Keep a Changelog, and this project adheres to Semantic
Versioning.

## [Unreleased]

### Added

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
