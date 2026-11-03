# Getting Started

This guide answers the questions a new visitor should be able to answer within about a minute:

- What is CacheFlow and what is its core differentiator?
- Which workload or operational pain does it address?
- What does it do versus what the model, tools, AKV, and serving system do?
- What prerequisites are needed for offline and live execution?
- What command runs a demo, and what files will be produced?
- How can the user inspect evidence, traces, checkpoints, and benchmark results?
- Which capabilities are implemented, experimental, or planned?

## Installation

```bash
pip install -e .
```

Python 3.12 required. Offline development needs no GPU. Dev dependencies (pytest) are declared separately and installed automatically by editable install.

## First Demo — VulnTriage

Run the end-to-end example using the demo fixture repository:

```bash
cacheflow run \
  --workflow vulntriage \
  --repo ./fixtures/demo_repo \
  --commit HEAD \
  --advisories ./fixtures/advisories.json \
  --out ./artifacts/run-001
```

Artifacts produced:

- `./artifacts/run-001/report.md`
- `./artifacts/run-001/report.json`
- `./artifacts/run-001/trace.jsonl`
- `./artifacts/run-001/latest.json` (checkpoint at each investigation boundary)

Inspect:

```bash
cacheflow inspect-run ./artifacts/run-001
cat ./artifacts/run-001/trace.jsonl
```

Validate before running:

```bash
cacheflow validate --workflow vulntriage
```

## What CacheFlow adds versus what the components already do

- **The DAG** ensures that node execution order is determined by validated code, not LLM choice.
- **AKV cache policy control** injects drop/reposition decisions explicitly into the request payload and protects verdict evidence from dropping.
- **Checkpoint and replay** preserve durable execution state independently of serving-system cache state.
- **Benchmark framework** produces machine-readable, reproducible measurements separating structural reproducibility from model-output reproducibility.

## Prerequisites

### Offline

- Python 3.12+, pip, pytest (dev deps auto-installed by editable install)

### Live AKV

- Compatible AKV/SGLang server running and reachable from this machine
- Pre-provisioned model ID and serving configuration in CLI flags or `.env`

## Listing capabilities

```bash
cacheflow capabilities
```

Shows registered workflows and each capability tagged `implemented` / `experimental` / `pending`.

## Troubleshooting

See `docs/troubleshooting.md`. Common causes: wrong workflow name, missing `--commit` argument, wrong `--repo` path escaping the fixture directory, and missing advisory file paths. All produce actionable `CacheFlowError` messages.
