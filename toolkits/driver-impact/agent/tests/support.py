from __future__ import annotations


def impact_document() -> dict[str, object]:
    return {
        "schema_version": 1,
        "task": "driver_change_impact",
        "snapshot": {
            "repository": "C:/repo",
            "base": {"requested": "HEAD", "commit": "abc"},
            "target": {"kind": "commit", "commit": "def"},
        },
        "profile": {"name": "test", "schema_version": 1, "sha256": "0" * 64},
        "packages": [{"name": "driver", "manifest": "Cargo.toml"}],
        "changes": [
            {
                "id": "C-001",
                "path": "src/driver.rs",
                "old_path": None,
                "status": "M",
                "old_sha256": "1" * 64,
                "new_sha256": "2" * 64,
                "binary": False,
                "patch": "- old\n+ new\n",
                "patch_truncated": False,
                "rule_ids": ["driver.transport"],
                "domains": ["transaction_sequencing"],
            }
        ],
        "domains": ["transaction_sequencing"],
        "authority_index": [
            {
                "id": "A-0001",
                "path": "docs/INVARIANTS.md",
                "kind": "heading",
                "heading_path": ["Invariants", "I-1 Exact traffic"],
                "text": "I-1 Exact traffic",
                "sha256": "3" * 64,
                "line": 3,
                "role": "invariants",
            }
        ],
        "obligations": [
            {
                "id": "O-001",
                "kind": "transaction_test_review",
                "strength": "required",
                "reason": "sequencing changed",
                "rule_id": "driver.transport",
                "change_refs": ["C-001"],
                "authority_refs": ["A-0001"],
                "checks": ["exact traffic"],
            }
        ],
        "unclassified": [],
        "ignored_paths": [],
        "suggested_commands": ["cargo test"],
        "warnings": [],
        "result": {"status": "review_required", "meaning": "review"},
    }


def ok_output() -> dict[str, object]:
    return {
        "status": "ok",
        "impacts": [
            {
                "kind": "transaction_order",
                "summary": "The sequence changed.",
                "change_refs": ["C-001"],
                "authority_refs": ["A-0001"],
                "obligation_refs": ["O-001"],
                "recommended_action": "Review exact traffic.",
                "confidence": "high",
                "requires_supervisor": False,
            }
        ],
        "unresolved": [],
    }
