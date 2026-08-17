# ph-changelog-agent

> [!WARNING]
> **Incubator-only source.** This is an experiment in limiting model authority,
> not a trusted agent, semantic verifier, or supported distribution. It is not
> intended for publication. See the repository
> [STATUS.md](../../../STATUS.md).

`ph-changelog-agent` is the contract-limited prose-worker experiment paired
with [`ph-changelog`](../core/README.md). It turns supervisor-supplied task
facts into contract-checked proposals, while delegating Markdown structure,
insertion, and final structural/profile checks to the core package.

The built-in changelog skill, style guide, few-shot examples, contract examples,
and JSON schemas are installed as package resources. Running from another
working directory therefore does not require copying an asset folder.

## Run with LM Studio

The model receives supervisor facts, selected skill material, and current
changelog prose. Do not include secrets. Prefer the loopback endpoint; an
overridden endpoint is a disclosure boundary and is not made trustworthy by
this client.

Start an OpenAI-compatible LM Studio server, then run:

```bash
uv run --locked ph-changelog-agent run \
  --facts toolkits/changelog/examples/task-facts-seqring.json \
  --profile photon-circus \
  --path CHANGELOG.md \
  --model coder
```

Add `--apply` to insert a successful result. The command snapshots the
changelog before the model call and checks it again immediately before
attempting a same-directory replacement. It refuses every intervening change
it observes, but an uncooperative writer can still race the final
check-and-replace window. A model response with
`status: needs_supervisor` exits `3` and is never applied.

Use `--apply` only in a clean, disposable, version-controlled copy after human
review. The snapshot covers the target changelog, not the source revision or
the freshness of evidence behind the supplied facts.

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

The runtime has no JSON Schema dependency. Its handwritten contract checks
enforce the packaged contracts, including required types, entry bounds,
allowed keys in model output, and uniqueness constraints. They also enforce
target-section authority, known fact IDs, and case-insensitive rejection of literal
`forbidden_claims` fragments. `allowed_claims` is prompt guidance; it is not a
semantic proof that generated prose follows from cited facts. Passing these
checks does not establish factual correctness, grounding, prompt-injection
resistance, provider trust, or safety.
