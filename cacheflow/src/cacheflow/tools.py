"""Deterministic repository tools for CacheFlow."""

import re
import os
from typing import Any, Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field
from pathlib import Path
from contextlib import contextmanager

from .errors import ToolExecutionError, ValidationError


@dataclass
class ToolResult:
    """Result of a tool execution."""

    name: str
    output: str
    truncated: bool = False
    truncated_marker: str = "..."
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "output": self.output,
            "truncated": self.truncated,
            "truncated_marker": self.truncated_marker,
            "metadata": self.metadata,
        }


# Byte cap constants for deterministic truncation
FILE_READ_CAP = 2000
REPO_Brief_CAPTION_SIZE = 500
DIR_LISTING_LIMIT = 100
MAX_GPGPATCH_LINE = 20000
SMOKE_TEST_LIMIT = 50


def truncate_output(text: str, max_bytes: int = FILE_READ_CAP, marker: str = "...", default: str = "") -> str:
    """Truncate output deterministically based on byte count."""
    if len(text.encode("utf-8")) <= max_bytes:
        return text
    result = text[:max_bytes - len(marker)]
    result = result + marker + "\n[truncated]"
    return result


class RepositoryTools:
    """Deterministic repository tools for vulnerability investigation."""

    def __init__(self, repo_path: Path):
        """Initialize tools with the repository root."""
        self.repo_root = repo_path.resolve()
        self.allowed_base = self.repo_root
        self._allowed_subdirs: Set[str] = set()

    def list_dir(self, name: str = ".", max_count: int = DIR_LISTING_LIMIT) -> Dict[str, Any]:
        """List directory contents deterministically."""
        try:
            full_path = self.allowed_base / name if not os.path.isabs(name) else self.repo_root / name
        except Exception as e:
            raise ValidationError(f"Invalid directory path: {e}")

        if not full_path.exists():
            return {"error": f"Directory not found: {full_path}"}
        if not full_path.is_dir():
            return {"error": f"Path is not a directory: {full_path}"}

        # Resolve allowed base and add subdirs
        entries = sorted(os.listdir(full_path))
        listing = [{"name": entry, "type": os.path.isdir(full_path / entry) and "dir" or "file"}
                   for entry in entries[:max_count]]

        return {"path": full_path, "entries": listing}

    def read_file(self, path: str) -> ToolResult:
        """Read a file deterministically."""
        try:
            full_path = self.allowed_base / path if not os.path.isabs(path) else self.repo_root / path
        except Exception as e:
            raise ValidationError(f"Invalid file path: {e}")

        if not full_path.exists():
            return ToolResult(name="read_file", output=f"File not found: {path}", truncated=False)
        if not full_path.is_file():
            return ToolResult(name="read_file", output=f"Not a file: {path}", truncated=False)

        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        return ToolResult(
            name="read_file",
            output=truncate_output(content),
            truncated=len(content.encode("utf-8")) > FILE_READ_CAP,
            metadata={"path": path, "size_bytes": len(content)},
        )

    def grep(self, pattern: str, path: Optional[str] = None, line_number: bool = True, ignorecase: bool = False, max_results: int = SMOKE_TEST_LIMIT) -> List[Dict[str, Any]]:
        """Grep for patterns deterministically."""
        try:
            search_root = (self.allowed_base / path) if path else self.repo_root
        except Exception as e:
            raise ValidationError(f"Invalid grep path: {e}")

        pattern_re = re.compile(pattern, re.IGNORECASE if ignorecase else 0)
        matches = []

        for root_dir, dirnames, filenames in os.walk(search_root):
            # Sort dir names for deterministic traversal
            dirnames.sort()
            for fname in sorted(filenames):
                if fname.startswith("."):
                    continue  # Skip hidden files
                fp = os.path.join(root_dir, fname)
                if not os.path.isfile(fp):
                    continue

                try:
                    with open(fp, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()

                    if line_number and fname != ".":
                        for i, line in enumerate(lines):
                            match = pattern_re.search(line)
                            if match:
                                pos = fp.replace(str(self.repo_root), "").lstrip("/").lstrip("\\")
                                rel_path = pos if pos else fname
                                matches.append({
                                    "file": rel_path,
                                    "line": i + 1,
                                    "match": match.group(),
                                    "context": lines[i].rstrip(),
                                })
                                if len(matches) >= max_results:
                                    break
                            else:
                                continue
                        if len(matches) >= max_results:
                            break
                except (OSError, UnicodeDecodeError):
                    continue

        # Sort matches deterministically by file, then line
        matches.sort(key=lambda m: (m["file"], m["line"]))
        return matches

    def symbol_map(self) -> Dict[str, Any]:
        """Build a deterministic import symbol map."""
        import_map = {}
        for root_dir, dirnames, filenames in os.walk(self.repo_root):
            dirnames.sort()
            for fname in sorted(filenames):
                if not fname.endswith(".py"):
                    continue
                filepath = os.path.join(root_dir, fname)
                rel_path = filepath.replace(str(self.repo_root), "").lstrip("/").lstrip("\\")

                module_prefix = rel_path.replace("/", ".").replace("\\", ".")
                if module_prefix.endswith(".__init__"):
                    module_prefix = module_prefix[:-len(".__init__")]

                try:
                    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()

                    # Find import statements
                    for match in re.finditer(r'(?:^|\n)\s*import\s+([\w.]+)', content):
                        imported = match.group(1)
                        if imported not in import_map:
                            import_map[imported] = {
                                "source_file": rel_path,
                                "imports": [],
                            }
                    for match in re.finditer(r'(?:^|\n)\s*from\s+([\w.]+)\s+import\s+([\w., ]+)', content):
                        from_mod = match.group(1)
                        to_import = match.group(2)
                        target_entry = import_map.get(from_mod)
                        if target_entry:
                            for sym in to_import.split(","):
                                sym = sym.strip().replace(" ", "")
                                if not sym:
                                    continue
                                if target_entry["imports"].append({"symbol": sym}) == [{"symbol": sym}] and sym not in ["*"]:
                                    pass

                except (OSError, UnicodeDecodeError):
                    continue

        return {"symbol_map": dict(import_map), "module_prefixes": sorted(import_map.keys())[:200]}

    def file_index(self, extensions: List[str] = None, exclude_generated: bool = True) -> List[Dict[str, Any]]:
        """Build a sorted file index."""
        exts = tuple([e.lower() for e in (extensions or ["py"])])
        files = []
        for root_dir, dirnames, filenames in os.walk(self.repo_root):
            dirnames.sort()
            for fname in sorted(filenames):
                if fname.startswith(".") or "\\" in fname or "/" in fname:
                    continue
                if not fname.lower().endswith(exts):
                    continue
                filepath = os.path.join(root_dir, fname)
                rel_path = filepath.replace(str(self.repo_root), "").lstrip("/").lstrip("\\")

                if exclude_generated and (".git" in filepath or "build" in filepath.lower() or "dist" in filepath.lower()):
                    continue
                if not exclude_generated and filepath.endswith("_generated.py"):
                    continue

                size = os.path.getsize(filepath)
                mtime = os.path.getmtime(filepath)
                files.append({
                    "path": rel_path,
                    "size": size,
                    "modified": mtime,
                })

        # Sort by path, size, modified time
        files.sort(key=lambda x: (x["path"], x["size"], x["modified"]))
        return files

    def build_briefing(self, file_index: List[Dict[str, Any]], advisory_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Build a concise repository briefing."""
        total_files = len(file_index)
        total_size = sum(f["size"] for f in file_index)
        largest = max(file_index, key=lambda x: x["size"]) if file_index else None

        briefing = {
            "repository": {
                "root": str(self.repo_root),
                "total_python_files": total_files,
                "total_size_bytes": total_size,
                "largest_file": None,
                "note_if_excluded": "Generated directories are excluded from the index.",
            },
            "advisory_summary": advisory_summary,
        }
        if largest:
            briefing["repository"]["largest_file"] = largest
        return briefing

    def generate_verdict(self, advisory: Dict[str, Any], evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a validated verdict for an advisory."""
        verdict_type = evidence[0]["snippet"][:3] if evidence else ""

        valid_verdicts = {"reachable", "not_reachable", "needs_human"}
        if verdict_type not in valid_verdicts:
            raise ValidationError(f"Invalid verdict type: {verdict_type}. Must be one of {valid_verdicts}")

        confidence = 0.5
        if verdict_type == "reachable":
            confidence = min(0.95, 0.3 + len(evidence) * 0.2)
        elif verdict_type == "not_reachable":
            confidence = min(0.95, 0.3 + len(evidence) * 0.2)

        verdict = {
            "advisory_id": advisory.get("id"),
            "package": advisory.get("package"),
            "verdict": verdict_type,
            "evidence": evidence,
            "reason": self.generate_reason(verdict_type, evidence, advisory),
            "fix": self.generate_fix(verdict_type),
            "confidence": round(confidence, 2),
        }

        # Validate schema before returning
        required_fields = ["advisory_id", "package", "verdict", "evidence", "reason", "fix", "confidence"]
        for field_name in required_fields:
            if field_name not in verdict:
                raise ValidationError(f"Verdict missing required field: {field_name}")

        return verdict

    def generate_reason(self, verdict: str, evidence: List[Dict[str, Any]], advisory: Dict[str, Any]) -> str:
        """Generate a deterministic reason string."""
        pkg = advisory.get("package", "unknown")
        if verdict == "reachable":
            sample = evidence[0]["snippet"] if evidence else "N/A"
            return f"Repository code contains '{sample}' which matches the vulnerability pattern documented in GHSA-{advisory.get('id', 'unknown')}. The finding is reachable under this configuration."
        elif verdict == "not_reachable":
            deps = advisory.get("dependencies", [])
            directly_used = any(d in deps for d in ["import", "from"])
            sample = evidence[0]["snippet"] if evidence else "N/A"
            if not directly_used:
                return f"No direct dependency on '{sample}' is configured; dependency path is not used in current code."
            return f"The vulnerable library referenced by '{sample}' is available in dependencies but not directly imported in the analyzed source files."
        return "Investigation inconclusive; further tool inspection recommended."

    def generate_fix(self, verdict: str) -> str:
        """Generate a recommendation fix."""
        if verdict == "reachable":
            return "Replace unsafe deserialization or globbing with explicit allowlisted paths and safe parse parsing."
        elif verdict == "not_reachable":
            return "Consider removing the unused vulnerable dependency entirely."
        return "Manual verification recommended due to investigation scope limitations."

    @staticmethod
    def validate_path(path_str: str, base_root: Path) -> Path:
        """Validate that a path is within the allowed base."""
        raw = Path(path_str)
        if raw.is_absolute():
            candidate = raw
        else:
            candidate = base_root / raw

        try:
            resolved = candidate.resolve()
        except Exception:
            raise ValidationError(f"Invalid path: {path_str}")

        if not str(resolved).startswith(str(base_root)):
            raise ValidationError(f"Path escapes repository root: {path_str}")
        return resolved
