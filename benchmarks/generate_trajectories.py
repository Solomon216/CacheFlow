"""Generate deterministic synthetic benchmark workloads for CacheFlow."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def build_workloads() -> list[dict]:
    return [
        {"name": "B0-baseline", "id": "b0", "dataset": "synthetic", "latency_ms": 120, "cache_ops": 8, "confidence": 0.88, "status": "pass"},
        {"name": "B1-reference-policy", "id": "b1", "dataset": "synthetic", "latency_ms": 96, "cache_ops": 6, "confidence": 0.92, "status": "pass"},
        {"name": "B2-integrated-policy", "id": "b2", "dataset": "synthetic", "latency_ms": 88, "cache_ops": 5, "confidence": 0.95, "status": "pass"},
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic benchmark trajectories")
    parser.add_argument("--out", default="benchmarks/workloads/synthetic.yaml")
    args = parser.parse_args()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"workloads": build_workloads()}
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Generated synthetic workload config: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
