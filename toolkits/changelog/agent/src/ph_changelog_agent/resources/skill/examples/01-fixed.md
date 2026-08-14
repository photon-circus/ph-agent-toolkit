### Input facts

- F1: A polling loop could keep extending its goal while the producer remained ahead.
- F2: The implementation now snapshots the goal once at call entry.
- F3: New publications wait for the next call.
- F4: Unit tests and Loom pin the behavior.
- Authorized section: Fixed.

### Correct output

```json
{
  "status": "ok",
  "entries": [{
    "section": "Fixed",
    "text": "`poll_up_to` now snapshots its drain goal once at call entry, preventing continuous producer activity from extending one invocation indefinitely; publications arriving after that snapshot wait for the next call. The bounded behavior is pinned by unit tests and Loom.",
    "fact_ids": ["F1", "F2", "F3", "F4"]
  }]
}
```
