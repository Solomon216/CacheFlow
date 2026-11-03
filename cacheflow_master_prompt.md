# Master Engineering Prompt: CacheFlow
## A Deterministic Agent Runtime with AKV KV-Cache Engineering

You are a senior Python systems engineer, LLM inference engineer, distributed workflow architect, and open-source maintainer.

Your task is to build **CacheFlow**, a working, well-tested, open-source Python project that combines deterministic DAG execution, AKV-based KV-cache management, checkpointing, replay, and reproducible benchmarking for long-running tool-using AI agents.

Do not produce only an architecture proposal, code snippets, pseudocode, or a skeleton repository. Implement a functional application with automated tests, documentation, a runnable example, and benchmark tooling.

Work incrementally. Verify each phase before proceeding. Inspect the actual dependencies and their APIs rather than inventing interfaces. Record implementation limitations and test results honestly.

---

# 1. Project Identity and Goals

**Project name:** CacheFlow

**Category:** Deterministic agent execution runtime and KV-cache engineering framework.

**Primary programming language:** Python 3.12, unless the installed AKV requirements establish a different compatible version.

**Primary inference backend:** AKV running on its compatible SGLang serving system.

**Primary demonstration application:** VulnTriage, an agent that investigates dependency vulnerability advisories against a pinned Python repository.

## 1.1 Core problem

Long-running LLM agents perform many tool calls and accumulate large conversation histories containing file contents, command output, logs, intermediate observations, and reasoning-related messages.

As the trajectory grows, inference can become expensive or slow, and the active KV cache can consume substantial memory. Removing old messages from the conversation and rebuilding the prompt can invalidate prefix reuse and require re-prefilling retained context.

CacheFlow should explore a more controlled approach:

1. Define agent execution using a deterministic DAG.
2. Maintain a complete, append-only conversation history.
3. Use AKV to execute explicit KV-cache drop and reposition operations.
4. Preserve authoritative workflow outputs independently of the model's active context.
5. Save checkpoints containing execution state and cache-operation history.
6. Resume interrupted runs through a validated recovery procedure.
7. Benchmark correctness, quality, cache behavior, latency, and resource utilization.

## 1.2 Core USP

CacheFlow's defining contribution is the combination of:

- **Deterministic DAG execution**
- **AKV-based KV-cache engineering**
- **Checkpoint and replay semantics**
- **Automated correctness and performance benchmarks**

Do not claim that CacheFlow invented AKV, deterministic workflow orchestration, or durable execution. Its contribution must be demonstrated through how these capabilities are integrated, tested, measured, and exposed as a reusable runtime.

## 1.3 Product discoverability and user-facing capability communication

CacheFlow must be understandable to developers who encounter the repository for the first time. Do not present it only as an internal runtime or a list of implementation details. The README and examples must make clear what CacheFlow does, which demands it addresses, who should use it, how to try it, and what outputs to expect.

### Product positioning

Use a concise, accurate positioning statement along these lines:

> CacheFlow is an open-source runtime for controlled execution of long-running AI workflows, combining deterministic DAG orchestration, AKV KV-cache management, checkpoint/replay, and reproducible benchmarking.

Keep **deterministic DAG execution and AKV KV-cache management** central to the project's identity. Checkpoint/replay and benchmarking demonstrate the value of integrating those capabilities. Do not imply that CacheFlow itself is an autonomous universal bug detector, and do not claim performance improvements before measuring them.

### User demands and example applications

Explain the user problem, the relevant CacheFlow capability, and the expected evidence/output for each use case:

1. **Repository analysis and bug investigation** — inspect a pinned local repository, map files and symbols, trace dependencies and call paths, formulate bug hypotheses, run safe targeted tests, and produce evidence-backed findings. Include exact file/line references when available and distinguish confirmed defects from hypotheses.
2. **Database and ETL incident investigation** — use explicitly configured, preferably read-only diagnostic tools to inspect SQL models, logs, batch watermarks, row counts, join behavior, and data-quality checks. Produce a timeline, quantified impact where evidence supports it, root-cause hypotheses, verification queries, and regression-test suggestions. Never imply that CacheFlow can access a production database without a user-configured connector and authorization.
3. **Long-running tool-using AI workflows** — coordinate dependent tasks, preserve durable workflow state, resume from checkpoints, and track tool execution to reduce unnecessary repeated work after interruption.
4. **Inference and KV-cache policy evaluation** — run controlled workloads through the required compatible AKV/SGLang path and compare cache policies using measured operation traces, latency, token usage, and available memory metrics.

These are application examples built on CacheFlow's runtime, not proof that the runtime independently performs all domain reasoning. The LLM, domain tools, data sources, prompts, and verification tests supply the investigation capabilities.

### Required developer experience

The repository must include a capability-discovery path, not just installation steps. A new user should be able to answer within about a minute:

- What is CacheFlow and what is its core differentiator?
- Which workload or operational pain does it address?
- What does it do versus what the model, tools, AKV, and serving system do?
- What prerequisites are needed for offline and live execution?
- What command runs a demo, and what files will be produced?
- How can the user inspect evidence, traces, checkpoints, and benchmark results?
- Which capabilities are implemented, experimental, or planned?

Include a concise capability matrix with columns such as **user demand**, **CacheFlow capability**, **required integrations**, **demo/command**, and **evidence/output**. Clearly label offline/mock demonstrations versus live AKV results.

### User-facing outputs

Examples should show representative terminal output and the schema or a sample of generated artifacts, including as appropriate:

- `report.md`: readable findings, evidence, severity/confidence, limitations, and recommended verification steps.
- `report.json`: machine-readable findings and run metadata.
- `trace.jsonl`: ordered task, tool, checkpoint, and cache-operation events.
- checkpoint files: durable execution state and recovery metadata, not a promise that server-side GPU KV cache survives a restart.
- benchmark summaries: configuration, workload identity, correctness results, latency, token counts, cache-operation counters, and available resource measurements.

Sample output must be explicitly marked **illustrative** unless generated by a real run. Never fabricate benchmark values, successful findings, or cache operations.

## 1.4 Project success criteria

The project is successful when:

- The DAG has explicit, validated execution order and transitions.
- Live inference requests pass through a compatible AKV server.
- AKV cache-operation requests are generated through the upstream API and actually executed.
- The full message history remains available in serialized requests.
- Protected context cannot be selected for dropping by CacheFlow's policies.
- State can be checkpointed and restored correctly.
- Replay does not silently repeat completed external side effects.
- Offline tests run without a GPU.
- Live AKV benchmarks demonstrate real server-side cache operations.
- Results distinguish measured improvements from hypotheses.
- A new developer can install, test, understand, and run the example from the repository documentation.

---

# 2. Mandatory Architecture Constraints

These requirements are non-negotiable.

## 2.1 AKV is mandatory in the real execution path

Use the official AKV agent-side cache policy and a compatible AKV/SGLang inference server.

Before implementation, inspect the current upstream repository:

- https://github.com/thu-nics/AKV
- `README.md`
- `akv/system/README.md`
- `akv/agent/README.md`
- `akv/agent/policy.py`
- `examples/demo.py`
- The official dependency and installation configuration.

Verify any additional modules needed for cache-operation history serialization and restoration.

Document the exact upstream revision or commit used during development.

Use the official AKV interfaces where available, including the appropriate versions of:

- `CachePolicy`
- Policy triggers, selectors, and reposition rules
- Cache-operation history
- Explicit cache actions, if supported
- The SGLang-compatible request protocol.

The documented integration pattern includes processing a full request payload through `CachePolicy.process(...)` before submitting it to the serving system. Confirm the exact installed method signatures and arguments before using them.

Do not recreate AKV's internal cache engine.

Do not manually modify internal GPU KV-cache structures.

Do not fabricate cache metrics.

Do not silently fall back to an ordinary hosted model endpoint when AKV is unavailable.

If the AKV server is unreachable, report a clear execution error and preserve recoverable workflow state.

## 2.2 Deterministic DAG is mandatory

Use a graph definition that is explicit in code.

The graph must have:

- Named nodes
- Explicit directed edges
- Cycle detection
- Stable topological ordering
- Validated node dependencies
- Explicit node input and output contracts
- Defined failure and retry behavior
- A deterministic scheduling rule.

The LLM must not be permitted to modify the graph, create arbitrary workflow edges, or choose the next top-level node at runtime.

The initial graph may expand a repeated investigation subgraph according to validated input. This expansion must happen before execution, use a stable ordering, and be independent of LLM decisions. Persist the resulting graph definition and its version in the run state.

The graph's execution order must be testable without invoking a real model.

## 2.3 Preserve the complete conversation history

Maintain an append-only sequence of serialized model messages, including system, user, assistant, and tool messages.

Do not remove earlier messages from the request merely because AKV drops their cache entries.

Do not rewrite an earlier message after it has entered the history.

Use AKV's supported `drop_message` and `reposition` fields or corresponding documented abstractions.

Validate zero-based message indices against the exact serialized request history.

Document the difference between:

- Complete serialized conversation history
- Durable execution state
- Model-visible or active KV-cache state
- AKV cache-operation history.

## 2.4 Do not overclaim determinism

The runtime must make deterministic guarantees about graph construction, scheduling, tool-output normalization, cache-policy decisions under controlled inputs, and checkpoint restoration.

It must not promise byte-identical LLM text under all hardware and inference configurations.

A live model response may vary even with temperature zero and a fixed seed. Separate structural reproducibility from model-output reproducibility in tests and documentation.

---

# 3. System Architecture

Implement the project as modular Python packages.

## 3.1 Major components

### A. DAG engine

Responsibilities:

- Validate graph definitions.
- Calculate stable topological order.
- Execute eligible nodes according to the predefined schedule.
- Validate node inputs and outputs.
- Record node start, success, failure, and retry events.
- Create checkpoint boundaries.
- Reject invalid state transitions.

### B. Agent execution layer

Responsibilities:

- Build valid OpenAI-compatible message histories.
- Submit model requests to AKV.
- Handle model responses and tool calls.
- Validate tool arguments.
- Execute only registered tools.
- Normalize tool outputs deterministically.
- Enforce call limits and termination conditions.

### C. AKV cache controller

Responsibilities:

- Integrate the installed AKV policy interface.
- Classify messages by their purpose and lifetime.
- Track message-index ownership and node boundaries.
- Apply the configured cache policy at defined request points.
- Protect designated message indices.
- Preserve and restore cache-operation history.
- Record requested operations and server-confirmed usage metrics.

CacheFlow must not assume an operation succeeded just because it generated a request containing `drop_message` or `reposition`.

### D. Checkpoint and replay manager

Responsibilities:

- Persist workflow state after completed node and investigation substeps.
- Persist message history.
- Persist cache-operation history.
- Persist graph version, execution position and model configuration.
- Record already-completed tool operations.
- Restore a run from a validated checkpoint.
- Verify that resumed execution is consistent with the stored history.
- Detect incompatible or corrupt checkpoints.

### E. Trace and benchmark engine

Responsibilities:

- Record one structured event per relevant execution action.
- Record node transitions, model calls, tool calls and cache operations.
- Record available server usage metrics.
- Produce machine-readable traces.
- Aggregate benchmark results.
- Distinguish simulated tests from live AKV measurements.

---

# 4. Recommended Repository Structure

Create the following layout. Adjust file boundaries if necessary, but document architectural changes.

```text
cacheflow/
├── README.md
├── LICENSE
├── CITATION.cff
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── THIRD_PARTY_NOTICES.md
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .env.example
├── Makefile
│
├── docs/
│   ├── capabilities.md
│   ├── use-cases.md
│   ├── getting-started.md
│   ├── architecture.md
│   ├── deterministic-execution.md
│   ├── akv-integration.md
│   ├── checkpoint-and-replay.md
│   ├── cache-policy.md
│   ├── benchmarking.md
│   ├── reproducibility.md
│   └── troubleshooting.md
│
├── src/
│   └── cacheflow/
│       ├── __init__.py
│       ├── config.py
│       ├── dag.py
│       ├── scheduler.py
│       ├── models.py
│       ├── state.py
│       ├── events.py
│       ├── checkpoints.py
│       ├── replay.py
│       ├── messages.py
│       ├── tools.py
│       ├── model_client.py
│       ├── cache_controller.py
│       ├── cache_plan.py
│       ├── trace.py
│       ├── errors.py
│       └── cli.py
│
├── examples/
│   ├── vulntriage/
│   │   ├── README.md
│   │   ├── workflow.py
│   │   ├── nodes.py
│   │   ├── tools.py
│   │   └── prompts.py
│   ├── repository_analysis/
│   │   ├── README.md
│   │   └── workflow.py
│   └── db_incident/
│       ├── README.md
│       └── workflow.py
│
├── fixtures/
│   ├── demo_repo/
│   ├── advisories.json
│   └── expected_results.json
│
├── benchmarks/
│   ├── README.md
│   ├── generate_trajectories.py
│   ├── run_benchmark.py
│   ├── aggregate_results.py
│   ├── compare_runs.py
│   └── workloads/
│
├── tests/
│   ├── unit/
│   │   ├── test_dag.py
│   │   ├── test_state.py
│   │   ├── test_messages.py
│   │   ├── test_tools.py
│   │   ├── test_cache_plan.py
│   │   └── test_checkpoints.py
│   ├── integration/
│   │   ├── test_fake_server.py
│   │   ├── test_full_offline_run.py
│   │   └── test_resume.py
│   ├── acceptance/
│   │   └── test_vulntriage.py
│   └── gpu/
│       ├── test_akv_smoke.py
│       └── test_live_cache_operations.py
│
└── .github/
    ├── ISSUE_TEMPLATE/
    ├── PULL_REQUEST_TEMPLATE.md
    └── workflows/
        ├── tests.yml
        └── lint.yml
```

Keep runtime modules focused. Avoid creating giant files that combine graph execution, model transport, cache policy, and checkpoint persistence.

---

# 5. Core State and Data Models

Use typed Python models, preferably Pydantic when appropriate.

At minimum, define models for the following concepts.

## 5.1 Run configuration

Include:

- Run ID
- Workflow identifier and version
- Input manifest
- Model and serving configuration identifiers
- Graph definition hash
- Cache-policy configuration and version
- Call and token budgets where available
- Tool permissions
- Checkpoint directory or backend configuration
- Trace output location.

Never persist API secrets or unrestricted environment contents in a checkpoint.

## 5.2 Execution state

Include:

- Current node
- Completed nodes
- Failed node and error details
- Graph execution position
- Validated node outputs
- Per-node retry counts
- Current advisory or workload item
- Full message history
- Message-index metadata
- Cache-operation history
- Checkpoint version
- Event sequence number
- Run status.

## 5.3 Message classification

Classify message indices into three categories:

**Spine:** messages that later workflow stages require, such as system instructions, task definition, repository summary, advisory list, investigation boundaries and committed verdicts.

**Scratch:** temporary tool observations, such as grep results, file excerpts, directory listings and intermediate diagnostic outputs.

**Reasoning/tool-call history:** assistant messages used to initiate tool calls and preserve the trace of why a tool was called.

Treat these classifications as a policy mechanism, not a substitute for testing whether later stages actually need an observation.

The default cache policy must never drop spine messages or any other explicitly protected message.

If an essential fact must survive scratch cleanup, persist it as a validated node output or evidence artifact.

## 5.4 Checkpoint format

Each checkpoint should contain, as applicable:

- Schema version
- Run ID
- Parent checkpoint ID
- Graph definition and version
- Execution cursor
- Completed-node outputs
- Message history
- Message classifications and index metadata
- Cache-operation history
- Model and serving identifiers
- Tool execution ledger
- Trace sequence number
- Integrity checksum.

Use versioned, validated serialization.

Write checkpoints atomically: write to a temporary location, flush as appropriate, validate, then commit the checkpoint.

Do not mutate previously committed checkpoints.

Provide a schema migration or explicit incompatibility error when checkpoint versions do not match.

---

# 6. Deterministic DAG for VulnTriage

Use VulnTriage as the first end-to-end workload.

## 6.1 Input

The application accepts:

- A local Python Git repository
- A pinned commit
- An advisories JSON file compatible with the supported advisory schema
- An output directory
- Model, server and execution configuration.

The run must not need external network access to investigate the repository once the inputs are available.

Validate that the pinned commit exists and that repository paths remain within the allowed repository root.

## 6.2 Output

Produce both:

- `report.md`
- `report.json`

Each advisory verdict must include:

```json
{
  "advisory_id": "GHSA-example",
  "package": "example-package",
  "verdict": "reachable",
  "evidence": [
    {
      "file": "app/example.py",
      "line": 42,
      "snippet": "example_vulnerable_call()"
    }
  ],
  "reason": "Explanation grounded in repository evidence.",
  "fix": "Recommended remediation.",
  "confidence": 0.0
}
```

Valid verdicts:

- `reachable`
- `not_reachable`
- `needs_human`

Validate output schemas and evidence references before writing the final report.

Do not invent file paths, line numbers, package behavior, or test results.

## 6.3 Graph definition

Implement the following execution sequence:

```text
N0: ingest
  |
N1: repo_map
  |
N2: brief
  |
N3[0]: investigate first sorted advisory
  |
N3[1]: investigate second sorted advisory
  |
N3[2]: investigate next advisory
  |
... one investigation instance per advisory
  |
N4: cross_check
  |
N5: render
```

The graph expansion and topological order must be determined before execution from validated inputs and fixed code.

Sort advisories deterministically by `(package, advisory_id)`.

Do not parallelize the investigation nodes in the initial version. They share the ordered conversation history and a single AKV cache-management sequence.

A node or tool must not be able to dynamically modify the graph.

### N0 — Ingest

- Validate inputs.
- Resolve the pinned repository commit.
- Load and validate advisory records.
- Sort advisories.
- Initialize state.

### N1 — Repository map

- Build a sorted file index.
- Build a deterministic import map.
- Exclude irrelevant build artifacts and generated data.
- Keep the repository summary under a configurable size cap.
- Record how omitted files are represented.

### N2 — Brief

- Send the repository map, task definition and advisory summary to AKV.
- Initialize the shared conversation history.
- Validate the response format.
- Record the completed node output.

### N3 — Investigation

Use a fixed tool interface:

- `grep`
- `read_file`
- `list_dir`
- `read_advisory`
- `submit_verdict`

Enforce a configurable maximum number of model turns per investigation.

Investigations must terminate on a valid verdict submission or a bounded failure path resulting in `needs_human`.

Make tool ordering, path handling, file excerpts and output truncation deterministic.

At every investigation boundary, persist the result and the updated state.

### N4 — Cross-check

- Examine the validated advisory verdicts.
- Identify contradictions and unsupported claims.
- Use an explicitly defined correction procedure.
- Validate any revised verdict against the output schema.
- Record all revisions as new events rather than mutating earlier history.

### N5 — Render

- Generate `report.json`.
- Generate `report.md`.
- Sort results deterministically.
- Include evidence, reason, recommended fix and confidence.
- Do not use an LLM to render the final JSON or Markdown if deterministic code can do so.

---

# 7. AKV Cache Policy

Create a dedicated, testable cache-policy module.

The initial policy should follow these principles.

## 7.1 Within-node scratch management

After the configured number of tool turns, drop eligible scratch-message KV entries that fall outside the retention window for the current investigation.

The initial experimental setting may retain the most recent 12 completed tool turns, but this must be configurable and justified as a benchmark parameter, not hard-coded as universally optimal.

The policy must select only eligible scratch entries.

## 7.2 Reposition

Reposition retained cache entries after the configured number of additional turns, following AKV's supported policy semantics.

The initial experiment may begin repositioning after turn 12 and then every 4 turns. Verify all behavior against the installed upstream AKV implementation.

## 7.3 Node-boundary cleanup

At the end of an investigation:

- Persist the validated verdict and evidence.
- Select only eligible remaining scratch entries from that investigation.
- Schedule the relevant cache drop and reposition operations using documented AKV APIs.
- Preserve protected messages.
- Record the resulting cache-operation history.

The next investigation must not accidentally inherit unprotected scratch from the previous investigation as active context.

## 7.4 Cross-check entry and exit

At cross-check entry, reposition only when required by the verified policy and serving semantics.

At cross-check exit, clean up its temporary context according to the configured policy.

Never drop verdicts or evidence artifacts needed for report rendering.

## 7.5 Policy abstraction

Implement the planned operation logic as pure, unit-testable functions where possible.

Example conceptual interface:

```python
actions_for(node, turn, state) -> CacheDecision
```

This is a proposed CacheFlow interface, not an assertion about AKV's API.

A CacheDecision should be validated against:

- Current node ownership
- Message-index bounds
- Protected-message set
- Existing hidden/dropped entries
- Previously scheduled operations
- Upstream policy capabilities.

Use AKV's real CachePolicy and CacheOperationHistory interfaces for actual request preparation.

If a proposed operation cannot be represented safely by the installed AKV API, document the limitation and redesign that policy step instead of inventing support.

---

# 8. Checkpointing, Recovery and Replay

Checkpointing is part of the core architecture, not a convenience feature.

## 8.1 Checkpoint boundaries

Persist state after:

- Graph initialization
- Completion of each node
- Completion of each investigation substep
- Each validated verdict submission
- Cross-check completion
- Final report generation.

Additionally, record model requests, tool results, cache decisions and recovery-related events in the trace.

## 8.2 Resume procedure

A resume operation must:

1. Load and validate the requested checkpoint.
2. Verify the schema and graph version.
3. Verify input and configuration identity.
4. Restore message history and cache-operation history.
5. Restore the event sequence and tool execution ledger.
6. Determine whether the current AKV server is compatible with the stored execution state.
7. Continue from the last valid completed boundary.
8. Persist new checkpoints as execution advances.

Never assume that a client checkpoint automatically restores the server's internal GPU KV cache.

Investigate the upstream AKV implementation's actual support for server restart and cache-state recovery. Implement only a documented recovery strategy. If the serving process has lost required cache state and the upstream interface does not support restoring it directly, fail safely or use a validated reinitialization procedure that preserves logical execution correctness.

Document any added latency or recomputation during recovery.

## 8.3 Duplicate side-effect prevention

Tool execution must have a durable execution ledger.

For each tool action, record:

- Deterministic action ID
- Node and run identifiers
- Canonicalized tool name and arguments
- Execution status
- Validated output or failure
- Checkpoint reference.

During replay, reuse committed tool results rather than repeating completed side effects.

The initial VulnTriage tools should be read-only wherever possible.

A replay system must distinguish reusing a recorded model response from making a new LLM call. Model outputs cannot be guaranteed identical when recomputed. Tests should use a scripted server so that replay semantics can be verified deterministically.

---

# 9. Structured Tracing and Observability

Write JSONL events with a versioned schema.

Include events for:

- Run created
- Graph constructed
- Node started
- Node completed
- Node failed
- Tool requested
- Tool executed
- Model request sent
- Model response received
- Cache operations planned
- Cache operations sent
- Cache usage reported
- Checkpoint committed
- Resume attempted
- Resume succeeded or failed
- Final report created.

Record, where available:

- Run and node IDs
- Event sequence number
- Timestamp
- Model identifier
- Request and response sizes
- Latency measurements
- Prompt and completion token counts
- Cached token counts
- `drop_skipped_tokens`
- `repos_tokens`
- Cache policy version
- Drop and reposition indices
- Checkpoint ID.

Follow AKV's documented usage-field names for the selected version.

Never record secrets, environment dumps, credentials or unredacted authorization headers.

Trace logging must make clear whether a cache operation was merely planned, included in a request, or confirmed through available server evidence.

---

# 10. Testing Strategy

The project must have a complete CPU-only test suite.

A GPU must not be required to install development dependencies, run unit tests, run the fake-server integration suite or execute standard CI.

## 10.1 DAG tests

Test:

- Graph construction.
- Expected topological order.
- Cycle rejection.
- Invalid edge rejection.
- Invalid node input/output rejection.
- Stable graph serialization.
- Stable graph hashing.
- Stable ordering of repeated investigation nodes.

## 10.2 Tool tests

Test:

- Stable file and directory ordering.
- Stable grep-hit ordering.
- Stable line-number reporting.
- Path traversal rejection.
- Stable output truncation.
- Byte caps and truncation markers.
- Deterministic tool serialization.
- Tool-argument validation.
- Repeated identical calls returning byte-identical output for an unchanged fixture.

## 10.3 Message and cache-policy tests

Test:

- Append-only message history.
- Correct zero-based message indices.
- Stable message classification.
- Protected messages are never selected for drop.
- No out-of-range indices.
- No invalid reposition triggers.
- Node-scoped selection never deletes another node's scratch unintentionally.
- The rolling retention policy works at its configured boundary.
- Node-exit cleanup includes all remaining eligible scratch.
- Reposition scheduling follows the configured policy.
- Cache decisions can be restored and reproduced.

## 10.4 Checkpoint and replay tests

Test:

- Checkpoint creation and loading.
- Atomic checkpoint writes.
- Corrupt checkpoint rejection.
- Schema-version mismatch.
- Run-ID and graph-version mismatch.
- Resume from every investigation boundary.
- No accidental reexecution of completed tool side effects.
- Consistent event numbering.
- Byte-identical remaining request payloads in controlled scripted runs.
- Clear handling when the AKV server state is no longer compatible.

## 10.5 Fake inference server

Build a scripted, OpenAI-compatible fake server that can:

- Return predefined assistant messages.
- Return predefined tool calls.
- Simulate model failures and timeouts.
- Record incoming request payloads.
- Simulate usage statistics for tests.
- Support repeatable replay scenarios.

Label all fake usage statistics as simulated. Never use them as results from the real AKV server.

## 10.6 Live AKV tests

Mark GPU or serving tests separately, such as:

```bash
pytest -m gpu
```

Test actual request acceptance and real cache operations through a compatible AKV/SGLang server.

Verify that the available server counters or traces substantiate that drop and reposition operations occurred.

The live test suite must not be reported as passing unless it was actually executed against the real server.

---

# 11. Benchmarking Framework

The repository must provide reproducible scripts and machine-readable results.

## 11.1 Benchmark configurations

Implement these configurations.

### B0 — Baseline

- Deterministic CacheFlow DAG.
- Same workload, prompts and tools.
- No CacheFlow-scheduled AKV drop/reposition operations.

Use the same AKV server when comparing cache-operation effects, while accounting for any ordinary caching behavior. Where practical, add a separate standard SGLang baseline to distinguish serving differences from cache-policy effects.

### B1 — Reference AKV policy

- Same DAG.
- Same workload.
- AKV's documented reference or rolling-window policy.
- All supported cache operations enabled.

### B2 — CacheFlow integrated policy

- Same workload.
- CacheFlow-managed protected-message rules.
- Node-scoped cleanup.
- Checkpoint and replay instrumentation.
- AKV operations enabled.

### B3 — Alternative policy experiments

Add only after B0–B2 work.

Test alternatives such as:

- Different tool-turn retention windows.
- Token-triggered cleanup.
- Different reposition intervals.
- Node-boundary cleanup.
- Hybrid token and node-boundary policies.

Keep policy configuration explicit and versioned.

## 11.2 Workloads

Create three benchmark families.

### Family A — Synthetic trajectories

Generate repeatable scripted agent sessions with 20, 40 and 80 tool turns.

Vary:

- Tool-result lengths.
- Number of files inspected.
- Number of tool results containing relevant evidence.
- Amount of irrelevant intermediate context.
- Checkpoint frequency.
- Failure location.

### Family B — VulnTriage fixtures

Create a realistic small Python repository and advisory fixture.

Include known cases such as:

- Reachable unsafe YAML loading.
- Reachable unsafe deserialization.
- Unsafe TLS verification.
- User-controlled template construction.
- Safe alternative API usage.
- Imports only in test helpers.
- Unused vulnerable dependency paths.
- Disabled code paths.

Include decoy files so some investigations exceed the initial cache-retention window.

Use ground-truth labels and evidence locations.

Start with eight advisories as a smoke test, but expand the fixture before making broad performance or quality claims.

### Family C — Recovery workloads

Inject failures:

- Before a node begins.
- Mid-investigation.
- After a tool result is received but before its commit.
- After checkpoint creation.
- At the investigation boundary.
- During report rendering.
- With the AKV server unavailable.
- After the serving process restarts.

Track which failures are recoverable and where the system must stop safely.

## 11.3 Metrics

Collect and report:

### Correctness

- Task success rate.
- Verdict accuracy.
- Evidence precision and recall.
- Valid structured-output rate.
- Replay mismatch rate.
- Recovery success rate.
- Duplicate side-effect count.
- Protected-message policy violations.

### Performance

- End-to-end wall-clock time.
- Time to first token.
- Time per output token.
- Per-node latency.
- Number of model requests.
- Number of tool calls.

### Token and cache behavior

- Prompt tokens.
- Completion tokens.
- Cached tokens.
- Dropped or skipped tokens.
- Repositioned tokens.
- Peak active context, if measurable through reliable telemetry.
- Cache-operation counts.

### Resource utilization

- Peak GPU memory, where available.
- CPU and memory use.
- Throughput for comparable workloads.

### Cost

- Actual inference cost when applicable and supported by known pricing.
- Serving time and compute consumption for self-hosted inference.

Do not use token count as a substitute for wall-clock time. Do not infer active-context reduction from cached-token ratios. Document what each metric actually measures.

## 11.4 Reporting

Every benchmark run must emit:

```text
results/
├── run.json
├── trace.jsonl
├── metrics.json
└── report.md
```

Create CSV aggregation for multiple runs.

The report must identify:

- Git commit
- Python version
- AKV commit/version
- SGLang version
- Model ID and revision, if available
- Hardware
- Workload and seed/configuration
- Number of repetitions
- Errors and excluded runs
- Median and variability for performance metrics
- Baseline-versus-treatment differences.

Use enough repeated runs to distinguish signal from noise. Report all failures and exclusions transparently.

Never hard-code claimed speedups or fabricate benchmark numbers in the README.

---

# 12. Open-Source Engineering Requirements

Produce a repository suitable for public release.

## 12.1 Dependencies

Use a `pyproject.toml` with:

- Clear runtime dependencies.
- Separate development dependencies.
- Optional benchmark dependencies where appropriate.
- Explicit Python version constraints.
- Reproducible dependency locking.

Inspect AKV's license and the licenses of all dependencies before selecting CacheFlow's license.

Choose a permissive license such as Apache-2.0 only after confirming compatibility and adding any required notices and attributions.

## 12.2 Code quality

Use:

- Type hints.
- Clear module boundaries.
- Structured exceptions.
- Consistent formatting.
- Static linting.
- Deterministic serialization.
- Explicit configuration.
- Helpful logging.
- Secure defaults.

Avoid overengineering a plugin framework before the core execution path is functional.

## 12.3 Documentation

The README must work as both a quick-start guide and a capability-discovery page. A new visitor should quickly understand what CacheFlow offers, what user demand it addresses, and how to validate the claims. Include:

1. A concise product positioning statement and explanation of the core differentiator: deterministic DAG execution plus AKV KV-cache management, supported by checkpoint/replay and benchmarking.
2. The problems CacheFlow is designed to address and who may benefit.
3. A capability matrix mapping user demand to capability, required integration, demo command, and resulting evidence/artifacts.
4. An architecture diagram showing the boundaries between CacheFlow, the LLM, domain tools, AKV, and the SGLang serving system.
5. Use-case summaries for repository bug investigation, database/ETL incident investigation, long-running tool-using agents, and inference/cache-policy benchmarking.
6. For each use case, an end-to-end example with input, command, representative output, generated files, and limitations. Keep the first working demo small and runnable.
7. Clear status labels for implemented, experimental, planned, mocked/offline, and live-server capabilities.
8. What AKV provides and what CacheFlow adds; do not imply CacheFlow replaces AKV or independently supplies all domain reasoning.
9. Supported environment and model requirements, with offline prerequisites separated from live AKV/GPU requirements.
10. Installation, offline tests, and exact commands to run the first example.
11. Starting a compatible AKV/SGLang server and running a live benchmark.
12. How to inspect report files, traces, checkpoints, and benchmark outputs.
13. Benchmark methodology, actual measured results when available, and explicit warnings that sample output is illustrative.
14. Current limitations, security/privacy considerations, and contribution instructions.

Add `docs/capabilities.md` and `docs/use-cases.md`. Each example README must answer: what demand it addresses, what inputs and permissions it needs, what CacheFlow coordinates, what the model/tools do, how to run it, what artifacts it emits, how to verify the result, and what is not yet supported.

Add an architecture document with an end-to-end sequence diagram.

Add a checkpoint document that explains which information belongs to durable state, complete message history, and the serving system's active KV cache.

Add a benchmark document with exact reproduction commands.

## 12.4 CI

Configure GitHub Actions to run CPU-only tests and lint checks on pushes and pull requests.

The standard CI workflow must not require a GPU or external model API key.

Live AKV tests should be marked separately and require an explicitly configured inference endpoint.

Do not make the public CI workflow depend on a private GPU server.

## 12.5 Security

Repository processing must be read-only unless an explicit future feature safely allows modifications.

Restrict filesystem tools to the selected repository root.

Never execute arbitrary LLM-provided shell commands without a defined allowlist or isolated execution boundary.

Never include secrets in source code, fixtures, traces or committed configuration files.

Keep untrusted repository content separate from system instructions and tool permissions.

---

# 13. CLI Requirements

Implement a usable command-line interface.

The exact syntax can be refined to fit the design, but support equivalent commands to:

```bash
cacheflow validate --workflow vulntriage
```

```bash
cacheflow test-offline
```

```bash
cacheflow run \
  --workflow vulntriage \
  --repo ./fixtures/demo_repo \
  --commit <PINNED_COMMIT> \
  --advisories ./fixtures/advisories.json \
  --out ./artifacts/run-001
```

```bash
cacheflow resume \
  --checkpoint ./artifacts/run-001/checkpoints/latest.json
```

```bash
cacheflow benchmark \
  --config benchmarks/workloads/synthetic.yaml \
  --out ./results/
```

```bash
cacheflow inspect-run ./artifacts/run-001
```

Validate arguments and provide actionable error messages. Add a capability-discovery command (for example, `cacheflow capabilities`) that lists available workflows, prerequisites, and which modes are offline/mock versus live AKV. Add concise help examples for supported use cases.

Provide user-facing commands or documented equivalent entry points for repository analysis and database incident investigation in addition to the VulnTriage demonstration. For example, a future CLI may support `cacheflow analyze-repo ...` and `cacheflow investigate-db ...`; implement only commands that are actually functional, and make unsupported connectors fail clearly rather than pretending to access data. The database example must use fixtures or an explicitly configured read-only connection by default.

Do not silently create placeholder reports when model execution or validation has failed. A failed run should preserve its trace and checkpoint and exit with an appropriate status.

---

# 14. Required Implementation Phases

Complete the project in the following order.

## Phase 1 — Upstream inspection and design

- Read the required AKV files.
- Inspect the public API, cache-policy components and history-serialization mechanisms.
- Confirm supported request fields and response metrics.
- Record compatibility requirements.
- Create `docs/architecture.md`.
- Create `docs/akv-integration.md`.
- Record unresolved questions in `NOTES.md`.

Do not start by guessing AKV method signatures.

## Phase 2 — Core models and DAG

- Implement state and graph models.
- Implement graph validation and stable topological order.
- Implement node contracts.
- Implement event logging.
- Implement deterministic serialization.
- Write unit tests.

All tests in this phase must run without a GPU.

## Phase 3 — Tools and VulnTriage fixtures

- Implement deterministic repository tools.
- Build the demo repository and advisory fixture.
- Implement validated verdict output.
- Add ground-truth acceptance tests.

## Phase 4 — AKV integration and cache policy

- Implement the model transport.
- Integrate the official AKV policy API.
- Implement the CacheFlow policy plan.
- Enforce protected-message rules.
- Record actual requests and usage metrics.
- Add a scripted fake-server suite.

Keep offline and live execution paths clearly separated.

## Phase 5 — Checkpoint and replay

- Implement versioned checkpoints.
- Implement validated resume logic.
- Implement the tool execution ledger.
- Simulate interruptions at each boundary.
- Verify remaining payload equivalence under scripted inputs.
- Explicitly test recovery behavior after AKV server restart or state loss.

## Phase 6 — End-to-end example

- Wire the complete DAG to the AKV model backend.
- Run the offline acceptance suite.
- Run live smoke tests if a compatible server and hardware are available.
- Generate a sample report and trace.
- Record which verification stages have and have not been executed.

## Phase 7 — Benchmarks

- Implement synthetic workloads.
- Implement B0, B1 and B2.
- Add metric collection and report generation.
- Validate metric provenance.
- Run measurements only where the required environment is available.
- Record measured results without estimating missing numbers.

## Phase 8 — Open-source release readiness

- Finalize README and documentation.
- Check license compatibility and dependency notices.
- Add CI, linting and formatting.
- Check for committed credentials and generated artifacts.
- Confirm all documented commands are accurate.
- Produce a release checklist and list any unfinished work.

---

# 15. Acceptance Criteria

The project is not considered complete until it satisfies all applicable requirements.

## Offline acceptance

1. The DAG order is stable and validated.
2. Cycles and invalid graph definitions are rejected.
3. Tool outputs are deterministic for identical fixtures.
4. Message history is append-only.
5. Protected indices never appear in CacheFlow-generated drop selections.
6. Cache policies are tested at every configured boundary.
7. Checkpoints are validated and versioned.
8. Resume behavior is verified across every investigation boundary.
9. Completed tool side effects are not silently repeated.
10. Replay tests produce the expected structural trace and requests under scripted inputs.
11. Corrupt and incompatible checkpoints fail safely.
12. The complete offline VulnTriage path produces schema-valid output.
13. CPU-only CI passes.

## Live AKV acceptance

1. The compatible AKV server starts using documented upstream instructions.
2. The selected model and serving configuration are supported.
3. The model request succeeds through the AKV endpoint.
4. Cache-operation fields are preserved in submitted requests.
5. Real cache operations are corroborated by available serving evidence.
6. Cache-operation history is saved and restored correctly according to the verified API.
7. Reported usage metrics come from the actual server response or trace.
8. The no-operation and AKV-enabled configurations can be compared using identical workload definitions.

## Benchmark acceptance

1. Workloads are reproducible.
2. Baseline and treatment configurations are documented.
3. Model, hardware and version details are saved.
4. Quality and performance metrics are separate.
5. Failed runs are recorded.
6. No performance improvement is claimed without measured evidence.
7. Sample outputs and aggregation scripts are provided.

Do not claim full acceptance when live AKV tests were not run. Clearly mark such requirements as pending hardware validation.

---

# 16. Required Deliverables

Produce:

1. Complete source code.
2. Installable Python package.
3. Deterministic DAG engine.
4. AKV integration.
5. Cache-policy implementation.
6. Checkpoint and replay implementation.
7. Scripted fake inference server for offline tests.
8. VulnTriage application and fixtures.
9. Ground-truth acceptance tests.
10. Synthetic benchmark workloads.
11. Live AKV benchmark scripts.
12. JSONL traces, JSON metrics and CSV aggregation.
13. README and architectural documentation.
14. Capability-discovery documentation and a user-demand-to-capability matrix.
15. Runnable repository-analysis and database/ETL incident-investigation examples, or explicit documented status if an integration cannot yet be implemented safely.
16. Representative sample outputs for each runnable example, clearly labeled illustrative unless produced by an actual run.
17. License and third-party notices.
18. Contributor and security documentation.
19. GitHub Actions workflows.
20. A sample VulnTriage report.
21. `NOTES.md` documenting exact versions, implemented behavior, test results, known limitations and unexecuted tests.

If the repository is in a working directory, edit the files there. Do not replace existing working code blindly: inspect it and preserve useful work.

Run the tests and linting commands in the available environment. Report exact commands and actual results.

---

# 17. Final Instructions to the Coding Agent

Start by inspecting the current AKV repository and documenting the integration plan.

Then implement the smallest end-to-end slice that can be tested: a fixed DAG, scripted tool calls, AKV-compatible request construction, one cache policy, and checkpoint/replay.

Expand from that working slice until all phases are implemented.

Do not stop after creating empty modules or documentation that describes functionality that is not implemented.

Do not substitute OpenRouter or another hosted endpoint for the required AKV path.

Do not substitute simulated cache metrics for live AKV measurements.

Do not add deployment or hosting infrastructure as a project requirement. CacheFlow is intended to be developed and published as an open-source repository; running GPU experiments can be a separate, explicitly documented requirement.

When a technical detail is uncertain, inspect the upstream code, test the installed API, or document the limitation. Do not invent behavior.

At completion, provide:

- A summary of the implementation.
- The final repository tree.
- The tests and checks that were actually executed.
- Exact commands to reproduce the offline demo.
- Exact commands to start the AKV server and run the live benchmark.
- Benchmark results actually measured, if available.
- Outstanding limitations and remaining work.

The end product must be a real, runnable, testable open-source project, not merely an architectural demonstration.
