# Checkpoint and Replay

Checkpointing is part of CacheFlow's core architecture, not a convenience feature. This document explains which information belongs to durable state, complete message history, and the serving system's active KV cache. CacheFlow never commits secrets to a checkpoint.

## Checkpoint boundaries

State is persisted after:

- Graph initialization
- Completion of each node
- Completion of each investigation substep
- Each validated verdict submission
- Cross-check completion
- Final report generation

Plus every tool execution is recorded in the tool execution ledger for side-effect replay. Every relevant action (node transitions, model calls, tool calls, cache decisions) is also recorded in the structured trace.

## Schema

Each checkpoint file contains:

| Field | Meaning |
|---|---|
| `schema_version` | `1.0`; mismatched checkpoints raise `CheckpointError` |
| `run_id` | Must match the requested run ID on resume |
| `graph_definition` | DAG definition used during this run |
| `execution_cursor` | Last completed node ID (resume from here) |
| `completed_outputs` | Per-node outputs from all completed nodes |
| `message_history` | Append-only conversation history |
| `message_classifications` | Index → classification map |
| `protected_indices` | Indices never selected for dropping |
| `cache_operation_history` | Plan + actual metrics per decision |
| `tool_execution_ledger` | Per tool call: canonical args, status, validated output |
| `trace_events` | Structured trace events up to checkpoint |
| `integrity_checksum` | SHA256 of the rest of the payload |

## Atomic writes

The manager writes to a `.tmp` file, flushes, validates, then atomically promotes via `os.replace`. Previously committed checkpoints are never mutated; a reversion pulls the latest valid checkpoint and applies it cleanly.

## Resume procedure

```
load checkpoint -> validate schema + graph version + run id -> restore RunState
        |
restore message history, classifications, protected indices, cache ops, tool ledger
        |
verify AKV server compatibility against stored config
        |
continue from last valid completed boundary, persist new checkpoints
```

Important caveats:

- A client checkpoint restores *logical* state only. The GPU KV cache stored inside the serving process is not automatically restored. When the serving process restarts, recomputation may add latency or recompute context. This is documented explicitly.
- `needs_human` verdicts are explicitly protected so cross-check cannot silently mutate them.
- Tool side effects are not repeated: duplicate calls return reused results unless the canonical args genuinely differ.

## Duplicate side-effect prevention

For each tool action, the record includes: deterministic action ID, node and run identifiers, canonicalized tool name and arguments, execution status, validated output, and checkpoint reference. During replay, the system reuses committed tool results rather than repeating completed side effects.

A replay system must distinguish reusing a recorded model response from making a new LLM call. Model outputs are not guaranteed byte-identical when recomputed; tests should use a scripted server so replay semantics can be verified deterministically.

## Corrupt and incompatible checkpoint handling

A checkpoint missing `schema_version`, an incompatible graph definition hash, an inconsistent `run_id`, or a corrupted checksum fails with `CheckpointError` and aborts resume rather than silently repairing state.
