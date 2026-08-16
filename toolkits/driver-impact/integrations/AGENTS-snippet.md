## Driver change-impact inspection

Before handing a non-trivial driver diff to a smaller worker, generate a
read-only impact document from the repository root:

```bash
uv run --locked ph-driver-impact inspect \
  --repo . --base HEAD --target worktree --output impact.json
```

Exit `3` means the document was generated and review is required. Review all
`required` and `supervisor_decision` obligations. Do not interpret `clear` as a
correctness verdict, and do not treat semantic mapper output as test or hardware
evidence.
