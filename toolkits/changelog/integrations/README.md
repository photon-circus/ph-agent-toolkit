# Changelog integration templates

These files are examples, not active policy for `ph-agent-toolkit`.

Before copying a template into another repository:

1. add `ph-changelog` to that repository's locked uv project;
2. select or create a policy profile;
3. verify the default and release branch names;
4. run validation against the repository's existing history;
5. keep agent execution outside CI unless the repository explicitly chooses a
   trusted provider and bounded fact source.

`github/changelog.yml` validates deterministic structure and protects released
history on ordinary pull requests. `git/` configures an optional local
semantic merge driver for additive `Unreleased` entries.
