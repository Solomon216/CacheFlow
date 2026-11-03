# CacheFlow Capabilities

This document maps the capabilities CacheFlow exposes and their readiness status. Each capability is categorized as **implemented**, **experimental**, or **pending** (documented in planning but not yet implemented).

## DAG orchestration

| Capability | Status | Description |
|---|---|---|
| Named nodes with directed edges | implemented | `DAG` class: validation, cycle rejection, stable topological order |
| Node input/output contracts | implemented | `NodeContract` dataclass; enforced during graph construction |
| Failure and retry behavior | implemented | Rejects invalid transitions; retry semantics available via scheduler |
| Deterministic scheduling rule | implemented | Kahn's algorithm with sorted deque leaves all ordering stable |

## Tool execution

| Capability | Status | Description |
|---|---|---|
| Deterministic file tools | implemented | `RepositoryTools`: list_dir, read_file, grep, file_index, symbol_map |
| Path traversal protection | implemented | Restricted to configured repository root |
| Output truncation | implemented | Byte-capped deterministic truncation with `...` marker |
| Replay of completed tool results | implemented | `ReplaySystem` deduplicates by canonicalized args |

## AKV cache management

| Capability | Status | Description |
|---|---|---|
| AKV integration via official API | experimental (mock), live when server is configured | `AKVModelClient` subclasses official endpoints; field names match upstream |
| Within-node scratch retention | implemented | `cache_plan.actions_for` selects eligible scratch beyond retention window |
| Reposition scheduling | implemented | Schedules reposition every `reposition_every` ticks past `reposition_after` |
| Node-boundary cleanup | implemented | `plan_investigation_exit` protects verdicts then drops remaining eligible scratch |
| Protected message enforcement | implemented | System/user messages default to protected indices |
| Cache operation history persistence | implemented | Recorded in checkpoint; never dropped silently on failover |

## Checkpoint and replay

| Capability | Status | Description |
|---|---|---|
| Versioned checkpoints | implemented | `CHECKPOINT_VERSION = "1.0"`; atomic temp+rename writes |
| Schema-version mismatch detection | implemented | Validation rejects incompatible checkpoints |
| Resume across investigation boundaries | implemented | `CheckpointManager.recover_state` restores state and cursor |
| Duplicate side-effect prevention | implemented | `ReplaySystem` records canonicalized arguments and results |

## Benchmarking

| Capability | Status | Description |
|---|---|---|
| Synthetic workload generation | implemented | `benchmarks/generate_trajectories.py` produces deterministic workload configs |
| Baseline run (B0) | implemented | `cacheflow benchmark` emits a baseline result summary |
| Reference policy run (B1) | implemented | Synthetic reference-policy benchmark output is available via config-driven runs |
| Integrated policy run (B2) | implemented | Integrated policy benchmark output is included in generated summaries |
| CSV aggregation | implemented | `benchmarks/aggregate_results.py` aggregates result CSVs |

## Database incident workflow

| Capability | Status | Description |
|---|---|---|
| Read-only connector CLI | implemented | `cacheflow analyze-db --schema ... --connection ...` emits inspection artifacts |
| SQL / log inspection artifacts | implemented | SQLite-backed read-only snapshots and markdown/JSON reports are generated locally |

## Quick self-check

```bash
cacheflow capabilities
```

Expected output lists the workflows registered and each capability status tagged `implemented` / `experimental` / `pending`.
