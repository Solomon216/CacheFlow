# CacheFlow

CacheFlow is a Python runtime for deterministic, auditable execution of long-running AI workflows. It combines deterministic DAG orchestration, append-only message history, checkpoint/replay, cache-policy control, and reproducible benchmarking.

The project is designed for workflows such as repository investigation, database incident analysis, and controlled cache-policy evaluation. It helps keep tool-using agents reproducible and traceable without losing the full execution history.

## Why CacheFlow?

Long-running agent workflows often accumulate large context windows, repeated tool operations, and hard-to-reason-about state transitions. CacheFlow addresses this by:

- enforcing deterministic execution order through a DAG
- preserving append-only message history for traceability
- protecting key messages from being dropped by cache policy
- storing workflow state in checkpoints for resume/replay
- generating benchmark summaries for comparison and regression tracking

## Features

- Deterministic DAG scheduling and validation
- Structured workflow state and execution metadata
- Append-only message tracking with protected-message handling
- Cache operation planning and replay-safe state management
- Offline and mock-compatible execution for local validation
- Benchmark and database-incident reporting commands

## Project status

This repository is a working open-source baseline for deterministic AI workflow execution. It is suitable for GitHub publication, local experimentation, and further extension, while still being intentionally focused on reproducibility and traceability over production-scale deployment complexity.

## Installation

Requirements:

- Python 3.12+
- pip

Install from the repository root:

```bash
python -m pip install -e .
```

## Quick start

Validate the built-in workflow:

```bash
cacheflow validate --workflow vulntriage
```

Run the demo workflow with the local fixture repo:

```bash
cacheflow run \
  --workflow vulntriage \
  --repo ./fixtures/demo_repo \
  --commit HEAD \
  --advisories ./fixtures/advisories.json \
  --out ./artifacts/run-001
```

Inspect the generated artifacts:

```bash
cacheflow inspect-run ./artifacts/run-001
cat ./artifacts/run-001/trace.jsonl
```

Run the offline test command:

```bash
cacheflow test-offline
```

## Benchmarking

Generate a deterministic synthetic benchmark set:

```bash
cacheflow benchmark \
  --config benchmarks/workloads/synthetic.yaml \
  --out benchmarks/results
```

The benchmark command produces a summary JSON and CSV report under the output directory.

## Database incident workflow

Run an offline read-only database inspection example:

```bash
cacheflow analyze-db \
  --schema demo \
  --connection "sqlite:///:memory:" \
  --out ./artifacts/db-demo
```

This emits a JSON/Markdown report that can be used for local incident walkthroughs and validation.

## Architecture overview

```text
+--------------------+      +------------------------+
| DAG engine         | ---> | Workflow state         |
| deterministic      |      | checkpoint/replay      |
+--------------------+      +------------------------+
          |                               |
          v                               v
+--------------------+      +------------------------+
| Tool execution     | ---> | Cache decision logic   |
| repository tools   |      | protected message ops  |
+--------------------+      +------------------------+
          |                               |
          v                               v
+--------------------+      +------------------------+
| Trace logger       |      | Benchmark / reports    |
+--------------------+      +------------------------+
```

## Documentation

- [Getting started guide](docs/getting-started.md)
- [Capabilities map](docs/capabilities.md)
- [Architecture overview](docs/architecture.md)
- [Checkpoint and replay](docs/checkpoint-and-replay.md)
- [AKV integration notes](docs/akv-integration.md)
- [Use cases](docs/use-cases.md)

## CLI reference

Common commands:

```bash
cacheflow --help
cacheflow validate --workflow vulntriage
cacheflow run --workflow vulntriage --repo <path> --commit <sha> --advisories <path> --out <dir>
cacheflow resume --checkpoint <path>
cacheflow benchmark --config <path> --out <dir>
cacheflow analyze-db --schema <schema> --connection <connection-string> --out <dir>
cacheflow inspect-run <run-dir>
cacheflow capabilities
```

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a PR.

## Security

Please review [SECURITY.md](SECURITY.md) for vulnerability reporting instructions.

## License

This project is licensed under the Apache 2.0 License. See [LICENSE](LICENSE).
