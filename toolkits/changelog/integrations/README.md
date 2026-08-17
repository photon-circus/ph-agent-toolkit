# Changelog integration templates

> [!WARNING]
> **Unsupported incubator templates.** These files are examples, not active
> policy, deployment guidance, release controls, or trusted integrations. See
> the repository [STATUS.md](../../../STATUS.md).

Before copying a template into another repository:

1. add `ph-changelog` to that repository's locked uv project;
2. select or create a policy profile;
3. verify the default and release branch names;
4. run validation against the repository's existing history;
5. define a repository-specific threat model, least privilege, accepted
   provider risk, operator-controlled facts, and a human approval point before
   considering agent execution.

`github/changelog.yml` exercises the current grammar/profile and compares
parsed released history on ordinary pull requests. It is not a sufficient
release or security control. `git/` configures an experimental local merge
driver for a narrow class of additive `Unreleased` entries.
