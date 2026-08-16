# ph-driver-impact-agent

`ph-driver-impact-agent` is the optional bounded semantic mapper for documents
produced by [`ph-driver-impact`](../core/README.md). A local model may connect
changed hunks to supplied authority and obligation IDs, but cannot establish
new facts, report checks as run, approve implementation correctness, interpret
physical evidence, or promote a capability.

Generate the exact model packet without contacting a model:

```bash
uv run --locked ph-driver-impact-agent packet --impact impact.json --output packet.json
```

Run an LM Studio-compatible local model:

```bash
uv run --locked ph-driver-impact-agent run \
  --impact impact.json --model coder --output semantic-impact.json
```

The default endpoint is `http://127.0.0.1:1234`; override it with
`LM_STUDIO_BASE_URL`. If the core used a custom profile, pass the same file to
`run --profile` so its digest can be checked. The command regenerates and
compares the core snapshot immediately before and after the model call.

Exit status `3` means the validated result is `needs_supervisor`; status `2` is
a contract, staleness, provider, or operational failure. Validate saved output
without a model using:

```bash
uv run --locked ph-driver-impact-agent check \
  --impact impact.json --output-document semantic-impact.json
```

All objects are closed and every model reference must name an ID present in the
core document. HIL evidence, capability claims, and unknown impacts always
retain explicit supervisor review.
