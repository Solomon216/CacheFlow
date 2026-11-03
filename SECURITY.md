# Security Policy

## Reporting a vulnerability

If you find a security vulnerability related to CacheFlow, please report it privately by emailing `security@example.com` — replace with the project's real contact. Do not post it publicly until it has been fixed.

The maintainers will acknowledge receipt and begin working on the fix within 48 hours. The disclosure timeline depends on the severity of the affected system.

## Important

CacheFlow's repository processing is read-only by default. It never writes to user repositories or executes arbitrary LLM-provided shell commands. Deterministic file tools are restricted to a configured repository root and reject path traversal attempts.

If you observe any of the following, do not engage:

- Any access to production infrastructure outside the explicitly configured AKV server endpoint.
- Evidence that secrets, credentials, or authorization headers were leaked in traces, checkpoints, or generated reports.

These should be reported directly through the security contact above, and the affected artifacts deleted immediately.
