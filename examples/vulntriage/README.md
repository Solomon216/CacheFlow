# VulnTriage — Repository vulnerability investigation

## What it addresses

Investigation of dependency vulnerability advisories against a pinned local repository.

## Inputs & permissions

- A local Python Git repository at `fixtures/demo_repo`
- A pinned commit (`--commit HEAD`)
- An advisories JSON file (`--advisories ./fixtures/advisories.json`)
- Optional output directory (`--out ./artifacts/run-001`)

The run does not need external network access once the inputs are available.

## How to run

```bash
cacheflow run \
  --workflow vulntriage \
  --repo ./fixtures/demo_repo \
  --commit HEAD \
  --advisories ./fixtures/advisories.json \
  --out ./artifacts/run-001
```

Use `cacheflow validate --workflow vulntriage` first to confirm the graph is well-formed.

## CacheFlow coordinates

CacheFlow provides a deterministic DAG (N0–N5), deterministic file tools, and AKV cache policy control. The LLM only reports verdict recommendations; the structured output schema is produced by deterministic code, not the model.

## Artifacts

- `report.md` — readable findings, evidence, severity/confidence, recommended verification steps.
- `report.json` — machine-readable findings and run metadata.
- `trace.jsonl` — ordered node, tool, and cache events.
- `latest.json` — checkpoint at each investigation boundary.

## Verification

Valid verdicts are one of `reachable`, `not_reachable`, or `needs_human`. Evidence references must point to existing files/lines in the fixture. Confidence values are in `[0.0, 1.0]`.

Status: **CPU-only offline** with mocked model; live AKV verification pending hardware.
