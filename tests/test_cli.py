import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_command(*args):
    return subprocess.run(["cacheflow", *args], cwd=str(ROOT), capture_output=True, text=True)


def test_validate_command_succeeds_for_vulntriage():
    result = run_command("validate", "--workflow", "vulntriage")
    assert result.returncode == 0, result.stderr
    assert "validated successfully" in result.stdout.lower()


def test_benchmark_command_emits_summary():
    out_dir = ROOT / "artifacts" / "pytest-benchmark"
    result = run_command("benchmark", "--config", "benchmarks/workloads/synthetic.yaml", "--out", str(out_dir))
    assert result.returncode == 0, result.stderr
    summary = out_dir / "summary.json"
    assert summary.exists(), "benchmark summary JSON should be generated"
    payload = json.loads(summary.read_text(encoding="utf-8"))
    assert payload["workloads"][0]["name"].startswith("B0")


def test_analyze_db_command_emits_reports():
    out_dir = ROOT / "artifacts" / "pytest-db"
    result = run_command("analyze-db", "--schema", "demo", "--connection", "sqlite:///:memory:", "--out", str(out_dir))
    assert result.returncode == 0, result.stderr
    report = out_dir / "db_incident_report.json"
    assert report.exists(), "database report JSON should be generated"
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["status"] == "read_only_snapshot"
