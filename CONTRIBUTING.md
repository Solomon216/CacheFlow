# CacheFlow Contributors

This project is free and open source under the Apache License 2.0.

Contributor Covenant Code of Conduct: see [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).

## Contribution Guidelines

1. Read and follow the contributing guidelines in [CONTRIBUTING.md](./CONTRIBUTING.md).
2. Submit a Pull Request with a clear description of the change, rationale, and testing steps.
3. Keep commits focused and incremental. Reference upstream AKV commit where relevant.
4. Add unit tests for each new capability; ensure the offline CI suite passes.
5. Add documentation for new public commands and new capabilities.
6. Never commit secrets. If you discover credentials, do not include them in any file.

## Code Quality

The repo uses type hints, structured exceptions, and consistent formatting throughout. Linting and formatting targets are specified in `pyproject.toml`; CI enforces them on every PR. Do not submit changes that fail lint.

## Testing

CPU-only tests must pass in CI. Live AKV tests are gated behind `pytest -m gpu` and must be explicitly executed against a compatible server.

## Design Principles

- Deterministic scheduling of DAG nodes; LLM does not choose the next top-level node.
- Append-only message history; earlier messages are never mutated or removed from serialized payloads solely because AKV drops their cache entries.
- Protected message indices are never selected for dropping.
- State lives in durable checkpoints, not in the serving system's GPU KV cache.
