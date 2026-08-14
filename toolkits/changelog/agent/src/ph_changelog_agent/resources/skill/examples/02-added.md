### Input facts

- F1: `EventFlags` is a 32-bit coalescing condition set.
- F2: Producer raise uses Release `fetch_or`.
- F3: Consumer take uses Acquire `swap(0)`.
- F4: Duplicate raises may coalesce.
- Authorized section: Added.

### Correct output

```json
{
  "status": "ok",
  "entries": [{
    "section": "Added",
    "text": "Added `EventFlags`, a 32-bit coalescing condition set whose producer raises conditions with Release `fetch_or` and whose consumer atomically takes and clears them with Acquire `swap(0)`; duplicate raises may coalesce.",
    "fact_ids": ["F1", "F2", "F3", "F4"]
  }]
}
```
