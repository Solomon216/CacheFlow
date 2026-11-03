# AKV Integration

CacheFlow integrates with the upstream [AKV project](https://github.com/thu-nics/AKV) through its official agent-side cache policy interfaces and a compatible AKV/SGLang serving system. AKV is mandatory in the real execution path; CacheFlow does not recreate its internal cache engine and never manually modifies GPU KV structures.

## Upstream reference

This build uses AKV development revision documented in `NOTES.md`. The exact revision is recorded there as of commit date `YYYY-MM-DD`.

## Supported interfaces

- **`CachePolicy`** — policy surface used to classify messages, select scratch indices, and trigger drop/reposition at each request point.
- **Policy triggers, selectors, and reposition rules** — operational rules called `scratch_retention`, `reposition_after`, `reposition_every`.
- **Cache-operation history** — recorded in `RunState.cache_operation_history` and persisted in checkpoints.
- **Explicit cache actions** — `drop_message` map and `reposition` list are forwarded verbatim into the model request payload via `AKVModelClient.send_request(..., extra_kwargs={"drop_message": ..., "reposition": ...})`.
- **SGLang-compatible request protocol** — AKV's official chat completion endpoint accepts these fields on the payload dict.

The cache controller processes a full request payload through `CachePolicy.process(...)` semantics by computing `CacheDecisionResult` locally (`cache_plan.actions_for`) before submitting the request. If a proposed operation cannot be represented safely by the installed AKV API, the limitation is documented and that policy step is redesigned instead of inventing support.

## Offline / mock execution path

When no live AKV server is configured, `MockModelClient` simulates the request round-trip. It does not perform real cache operations; only the plan records what *would* have been sent. Fake server tests assert that planned operations are correctly encoded in the serialized payload rather than performing real cache effects.

```python
from cacheflow.model_client import MockModelClient
mc = MockModelClient()
print(mc.is_available())   # False without a running server
```

Live path:

```bash
cacheflow run --workflow vulntriage \
  --repo ./fixtures/demo_repo \
  --commit HEAD \
  --advisories ./fixtures/advisories.json \
  --out ./artifacts/run-live \
  --server-url http://localhost:8000
```

## Cache operation persistence semantics

CacheFlow records cache-operation plans and actual response usage metrics. If an operation was merely included in the submitted request (planned), trace event `cache_operation_sent` is logged. If the server confirmed usage metrics (reported), `cache_usage_reported` is logged. Neither event is silently dropped.

Never assume that a client-side cache decision is authoritative: server-side counters or traces corroborate actual effects when available, and missing server evidence means missing verification in the acceptance criteria.
