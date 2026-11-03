# CacheFlow

CacheFlow is an open-source runtime for controlled execution of long-running AI workflows, combining deterministic DAG orchestration, AKV KV-cache management, checkpoint/replay, and reproducible benchmarking.

## Product Positioning

CacheFlow is an open-source runtime for controlled execution of long-running AI workflows, combining deterministic DAG orchestration, AKV KV-cache management, checkpoint/replay, and reproducible benchmarking.

## Core Differentiator

CacheFlow's defining contribution is the combination of:

- **Deterministic DAG execution**
- **AKV-based KV-cache management**
- **Checkpoint and replay semantics**
- **Automated correctness and performance benchmarks**

Unlike traditional runtime frameworks, CacheFlow tightly integrates deterministic workflow orchestration with explicit AKV-based cache policy control, ensuring reproducible execution for long-running tool-using AI agents.

## Problems Addressed

CacheFlow addresses the following operational pains:

1. **Repository analysis and bug investigation** — Inspect pinned repositories, trace dependencies, formulate bug hypotheses, run safe tests, and produce evidence-backed findings.
2. **Database and ETL incident investigation** — Use read-only diagnostic tools to inspect SQL models, logs, watermarks, data-quality checks, and produce evidence-backed findings.
3. **Long-running tool-using AI workflows** — Coordinate dependent tasks, preserve durable workflow state, resume from checkpoints, and track tool execution to reduce unnecessary repeated work.
4. **Inference and KV-cache policy evaluation** — Run controlled workloads through AKV/SGLang and compare cache policies using measured operation traces, latency, and memory metrics.

## Capabilities

CacheFlow provides the following core capabilities:

| User Demand | CacheFlow Capability | Required Integration | Demo Command | Evidence/Outputs |
|---|---|---|---|---|
| Repository analysis | Deterministic DAG with AKV cache management | AKV policy integration | `cacheflow run --workflow vulntriage --repo ./fixtures/demo_repo` | `report.md`, `report.json`, `trace.jsonl` |
| Database investigation | Configurable read-only connectors | Database plugin architecture | `cacheflow analyze-repo --schema <schema>` | Investigation artifacts and evidence |
| Long-running workflows | Checkpoint and replay | Durable state persistence | `cacheflow run --workflow <wf>` | Checkpoint files, trace history |
| Cache evaluation | AKV integration with policy testing | Live AKV/SGLang server | `cacheflow benchmark --config workloads/b0.yaml` | Benchmark metrics, cache-operation traces |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CacheFlow Runtime                    │
├─────────────────────────────────────────────────────────┤
│  DAG Engine      Agent Layer      AKV Controller       │
│  (graph,        (model transport, |  (cache policy,      │
│   scheduler)    tools, messages)  history, metrics)     │
└─────────────────────────────────────────────────────────┘
         │                        │                       │
┌─────────────────────────────────────────────────────────┐
│                    External Components                   │
├─────────────────────────────────────────────────────────┤
│  LLM/Model       Domain Tools       AKV/SGLang Server   │
│  (via AKV)       (deterministic)     (cache-aware)       │
└─────────────────────────────────────────────────────────┘
```

CacheFlow coordinates:
- **LLM inference** through AKV/SGLang-compatible endpoints
- **Domain tools** (grep, read_file, list_dir, etc.) via deterministic implementations
- **AKV cache management** with explicit drop/reposition operations
- **Workflow state** via checkpoints and traces

## Requirements

### For Offline Execution (CPU-only)

- Python 3.12+
- Rust/Cargo (for AKV native components)
- uv package manager
- Deterministic tools and fixtures

### For Live AKV Execution

- GPU-capable hardware
- Compatible AKV/SGLang server
- Running AKV instance with configured model
- Network connectivity to server

## Quick Start

### Install

```bash
# Clone the repository
cd ~/projects
.git clone https://github.com/thu-nics/CacheFlow.git
cd CacheFlow

# Install dependencies
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e .
```

### Run the First Demo (VulnTriage)

```bash
# Validate the workflow configuration
cacheflow validate --workflow vulntriage

# Run the end-to-end example using fixtures
cacheflow run \
  --workflow vulntriage \
  --repo ./fixtures/demo_repo \
  --commit <PINNED_COMMIT> \
  --advisories ./fixtures/advisories.json \
  --out ./artifacts/run-001

# Inspect the generated report
cat ./artifacts/run-001/report.md
```

### Inspect Run Artifacts

```bash
# View execution trace
cat ./artifacts/run-001/trace.jsonl

# View latest checkpoint
python3 -c "from cacheflow.checkpoints import load_checkpoint; import json; print(json.dumps(load_checkpoint('./artifacts/run-001/checkpoints/latest.json'), indent=2))"

# Run acceptance tests (CPU-only)
cacheflow test-offline
```

### Start AKV Server (for live tests)

```bash
# Follow AKV documentation for server setup
# Configure endpoints in settings.json
# Run live benchmarks with cacheflow benchmark
```

## Capabilities Matrix

| Capability | Offline/Mock | Experimental | Live AKV |
|---|---|---|---|
| DAG construction | ✅ | ❌ | ❌ |
| Deterministic tool execution | ✅ | ❌ | ❌ |
| Cache policy configuration | ✅ | ❌ | ❌ |
| Checkpoint and replay | ✅ | ❌ | ❌ |
| AKV integration | ❌ | ✅ (mock server) | ✅ |
| Live model inference | ❌ | ❌ | ✅ |
| Cache operation tracing | ✅ | ✅ | ✅ |
| Full workflow execution | ✅ (mock LLM) | ✅ (demo tools) | ✅ |

## Current Limitations

- Database connectors require additional configuration and implementation
- Real-world workflows may need custom tool integrations
- Performance characteristics depend on AKV server configuration
- Some deterministic guarantees assume fixed tool outputs

## Next Steps

1. **Phase 1** — Complete AKV integration documentation and design
2. **Phase 2** — Implement core models (state, graph, DAG engine)
3. **Phase 3** — Build deterministic tools and fixtures
4. **Phase 4** — Implement AKV integration and cache policies
5. **Phase 5** — Implement checkpoint and replay
6. **Phase 6** — Build end-to-end VulnTriage example
7. **Phase 7** — Implement benchmarks
8. **Phase 8** — Open-source release readiness

## How to Contribute

See [CONTRIBUTING.md](/CONTRIBUTING.md) for contribution guidelines, code quality standards, and testing requirements.

## License

See [LICENSE](/LICENSE) for project licensing information.

## References

- [AKV Repository](https://github.com/thu-nics/AKV)
- [SGLang Documentation](https://github.com/sgl-project/sglang)
- [Python Best Practices](https://docs.python.org/3.12/)