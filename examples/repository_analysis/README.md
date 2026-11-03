# Repository analysis demo (Phase B1)

This example describes the planned use case rather than an implemented workflow: static inspection of a pinned repository to identify potentially vulnerable code patterns.

## Status

Experimental. The core VulnTriage DAG supports the shared infrastructure (deterministic tools, DAG engine, cache controller), but this dedicated workflow has not been implemented yet. See `NOTES.md` for timeline details.

When implemented, the demo will accept `--repo`, `--commit`, and `--analysis-rules` arguments, produce a `report.json` and `trace.jsonl`, and be runnable via:

```bash
cacheflow run --workflow repo-analysis --repo ./fixtures/demo_repo --commit HEAD --out ./artifacts/ra-001
```

## Limitations

Current repository state focuses on VulnTriage. Extension work requires additional deterministic tool implementations (e.g., AST-based symbol scanning) and a writable decision procedure rather than read-only tool calls.
