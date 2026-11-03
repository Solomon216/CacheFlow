# Architecture — End-to-end sequence

## Sequence diagram

```text
+-------------------+        +------------------+        +-------------------+
|   DAG Engine      |<------>|  RunController  |<------>|  AKV Model Client |
| (validation,     |        | (orchestration,  |        | (official API)    |
|  scheduling)      |        |  trace, cache    |        |                   |
|                  |        |  decisions)      |        |                   |
+--------+---------+        +----+-------------+        +----------+----------+
         |                                    ^       |              ^
         v                                     |       v              |
+-------------------+        +------------------+        +-------------------+
| RunState          |        |    TraceLogger   |        |    Mock Model     |
| (messages,        |<------>| (JSONL events)  |<------>|    Model Client   |
|  protected idx,   |        |                  |        |  (offline tests)  |
|  cached ops,     |        +------------------+        +-------------------+
|  tool ledger)    |
+-------------------+                ^
                                         |
+-------------------+                    v
|CheckpointManager |        +-----------------------+        +-------------------+
|atomic writes,    |-------->|     AKV Model Client |<------->|  CacheController  |
|schema validation|         |                       |        |  (policy + ops)   |
+-------------------+        +-----------------------+        +-------------------+
                                                                        |
                                                              +-------+--------+
                                                              |  fake scripted   |
                                                              |    server        |
                                                              +-----------------+
```

## Module boundaries

### DAG engine (`dag.py`)

Owns node definitions, contract validation, topological sorting, and execution dispatch. Does not touch the model, tools, or cache controller directly.

### Agent execution layer (`state.py`, `tools.py`, `model_client.py`, `replay.py`)

`state.py` is the shared data model; `tools.py` is the deterministic tool surface; `model_client.py` handles transport (live AKV or mock); `replay.py` records reusable completed tool results. These modules cooperate through the `RunController`.

### AKV cache controller (`cache_controller.py`, `cache_plan.py`)

Owns policy planning as pure functions (`actions_for`, `plan_investigation_exit`) and the real `CachePolicy` integration surface when live AKV is configured. Tracks protected indices and cache-operation history.

### Checkpoint and replay (`checkpoints.py`, `replay.py`)

Owns versioned, validated state persistence and duplicate-side-effect prevention. Decoupled from the model layer so replay is independent of LLM responses.

### Structured tracing (`trace.py`, `events.py`)

Unified event source. Both the dag engine and the agent execution layer write through the same logger.

## End-to-end flow for a full run

1. **Graph construction** — `build_vuln_triage_graph` validates contracts, appends `N0`..`N5` nodes, records edges. Stable hash computed.
2. **Ingest** — resolve commit, load advisories, sort deterministically by `(package, advisory_id)` and initialize state.
3. **Repository map** — deterministic file index, import map, size cap enforced.
4. **Brief** — system/user messages appended to history; spine indices protected.
5. **Investigations (N3[*])** — scripted tool turns per investigation; every turn classified by role. At each boundary, `plan_investigation_exit` computes cache decisions; protected verdicts survive.
6. **Cross-check (N4)** — reviews verdicts, identifies contradictions, validates revised schema, records revisions as new events.
7. **Render (N5)** — deterministic JSON/Markdown from validated verdicts, no LLM involved.
8. **Finalization** — written `report.md`, `report.json`, final checkpoint committed.

## Dependencies

Runtime: `pydantic>=2.0`, `requests>=2.28`. Dev: `pytest>=7.4`. Optional benchmark tools installed by `pip install benchmark`.

## Serialization guarantees

- All `dataclasses` use frozen constructors where possible.
- Message history is append-only; earlier message indices are never mutated in place.
- Trace events are ordered by sequence number; events with higher sequence numbers always appear after lower ones.
- Checkpoints preserve complete message history plus cache-operation history, allowing replay of prior steps.
