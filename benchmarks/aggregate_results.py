"""Aggregate CSV benchmark results into a compact summary."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def aggregate(paths: list[Path]) -> list[dict]:
    rows: list[dict] = []
    for path in paths:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate benchmark CSV results")
    parser.add_argument("paths", nargs="+", help="CSV files to aggregate")
    parser.add_argument("--out", default="benchmarks/results/aggregate.csv")
    args = parser.parse_args()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = aggregate([Path(value) for value in args.paths])
    writer_fieldnames = sorted({key for row in rows for key in row})
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=writer_fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Aggregated {len(rows)} benchmark rows into {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
