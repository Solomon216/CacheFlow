# Database / ETL incident investigation demo (Phase C)

## What it addresses

Use explicitly configured, preferably read-only diagnostic tools to inspect SQL models, logs, batch watermarks, row counts, join behavior, and data-quality checks. Produce a timeline, quantified impact where evidence supports it, root-cause hypotheses, verification queries, and regression suggestions.

## Inputs & permissions

A configured database connector via environment variables or CLI flags. Never defaults to an unauthenticated production connection. Read-only by default.

## Status

Experimental. This demo is documented in planning but not implemented. The database example must use fixtures or an explicitly configured read-only connection by default. No `analyze-db` command exists yet.

## How to invoke when implemented

```bash
cacheflow analyze-db --schema <schema> --connection "<spec>" --out ./artifacts/db-incident-001
```

## Limitations

Requires external connector implementation not yet present in this build. Connector plug-ins are experimental.
