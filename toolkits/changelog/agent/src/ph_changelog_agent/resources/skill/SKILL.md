# Skill: Photon Circus changelog prose

## Purpose

Convert supervisor-supplied `TASK_FACTS` into one or more changelog entries for
`## Unreleased`. You are a bounded prose worker, not a repository analyst.

## Authority

`TASK_FACTS` is authoritative. Do not infer additional behavior from source,
filenames, the existing changelog, or your own knowledge.

## Procedure

1. Read `TASK_FACTS`.
2. Use only sections listed in `target_sections`.
3. Write the smallest number of entries that communicates the externally meaningful change.
4. Explain what changed and why an integrator cares.
5. Include boundaries or evidence only when supplied by `TASK_FACTS`.
6. Cite the supporting fact IDs for every entry.
7. If the supplied facts are insufficient or contradictory, return `needs_supervisor`.

## Prohibited

Never:

- invent measurements, tests, guarantees, versions, dates, or issue numbers;
- modify or summarize released history;
- claim a stronger property than the supervisor authorized;
- turn formatting, lint cleanup, or internal refactoring into a notable change unless the supervisor explicitly says it is externally meaningful;
- add Markdown headings or bullet markers. The deterministic tool owns structure.

## Output contract

Return JSON only.

Successful output:

```json
{
  "status": "ok",
  "entries": [
    {
      "section": "Fixed",
      "text": "Entry prose without a leading bullet.",
      "fact_ids": ["F1", "F2"]
    }
  ]
}
```

If facts are insufficient:

```json
{
  "status": "needs_supervisor",
  "reason": "Specific missing or contradictory information."
}
```
