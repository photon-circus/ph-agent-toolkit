# ph-changelog-agent

`ph-changelog-agent` is the bounded prose-worker companion to the deterministic
[`ph-changelog`](../core/README.md) package. It turns supervisor-supplied task
facts into validated changelog prose, but delegates Markdown structure,
insertion, and final validation to the core package.

The built-in changelog skill, style guide, few-shot examples, contract examples,
and JSON schemas are installed as package resources. Running from another
working directory therefore does not require copying an asset folder.

## Run with LM Studio

Start an OpenAI-compatible LM Studio server, then run:

```bash
uv run --locked ph-changelog-agent run \
  --facts toolkits/changelog/examples/task-facts-seqring.json \
  --profile photon-circus \
  --path CHANGELOG.md \
  --model coder
```

Add `--apply` to insert a successful result. The command snapshots the
changelog before the model call, checks it again immediately before an atomic
same-directory replacement, and refuses every intervening change it observes.
As with ordinary filesystem writes, an uncooperative writer can still race the
final check-and-replace window. A model response with
`status: needs_supervisor` exits `3` and is never applied.

The defaults can be overridden with:

```text
LM_STUDIO_BASE_URL
LOCAL_CHANGELOG_MODEL
PH_CHANGELOG_PROFILE
PH_CHANGELOG_SKILL_DIR
```

`--skill-dir` takes precedence over `PH_CHANGELOG_SKILL_DIR`, which takes
precedence over the packaged skill.

## Validate task facts without a model

```bash
uv run --locked ph-changelog-agent facts check \
  toolkits/changelog/examples/task-facts-seqring.json
```

The runtime has no JSON Schema dependency. Its handwritten validators enforce
the packaged contracts, including required types, entry bounds, allowed keys in
model output, and uniqueness constraints. They also enforce target-section
authority, known fact IDs, and case-insensitive rejection of literal
`forbidden_claims` fragments. `allowed_claims` is prompt guidance; it is not a
semantic proof that generated prose follows from cited facts.
