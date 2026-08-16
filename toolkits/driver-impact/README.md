# Driver change-impact toolkit

This toolkit turns a concrete local driver repository diff into a bounded
review packet. [`core`](core/README.md) performs all Git observation,
classification, indexing, and obligation generation deterministically. The
optional [`agent`](agent/README.md) package asks a local model to connect those
supplied facts without granting mutation, check execution, evidence judgment,
or capability-promotion authority.

The canonical flow is:

```text
local Git states
      ↓
ph-driver-impact JSON
      ↓
bounded semantic task packet
      ↓
validated local-model mapping or needs_supervisor
```

Checked-in [`examples`](examples/) demonstrate the core and agent contracts.
Downstream repositories may adapt the [`integration snippet`](integrations/AGENTS-snippet.md)
without making it policy for this workspace.
