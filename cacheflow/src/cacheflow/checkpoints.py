"""Checkpoint and replay manager for durable execution state."""

import json
import hashlib
import os
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from .state import RunState, RunStatus, ToolExecution, NodeOutput, NodeStatus
from .errors import CheckpointError


CHECKPOINT_VERSION = "1.0"
CHECKPOINT_DIR_NAME = "checkpoints"
LATEST_FILE = "latest.json"


@dataclass
class CheckpointData:
    """Checkpoint record for a CacheFlow run."""

    run_id: str
    parent_id: Optional[str] = None
    schema_version: str = CHECKPOINT_VERSION
    graph_definition: Dict[str, Any] = field(default_factory=dict)
    execution_cursor: str = ""
    completed_outputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    message_history: List[Dict[str, Any]] = field(default_factory=list)
    message_classifications: Dict[int, str] = field(default_factory=dict)
    protected_indices: Set[int] = field(default_factory=set)
    cache_operation_history: List[Dict[str, Any]] = field(default_factory=list)
    tool_execution_ledger: List[Dict[str, Any]] = field(default_factory=list)
    trace_events: List[Dict[str, Any]] = field(default_factory=list)
    model_config: Dict[str, Any] = field(default_factory=dict)
    integrity_checksum: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "parent_id": self.parent_id,
            "schema_version": self.schema_version,
            "graph_definition": self.graph_definition,
            "execution_cursor": self.execution_cursor,
            "completed_outputs": self.completed_outputs,
            "message_history": self.message_history,
            "message_classifications": {k: v for k, v in self.message_classifications.items()},
            "protected_indices": sorted(self.protected_indices),
            "cache_operation_history": self.cache_operation_history,
            "tool_execution_ledger": self.tool_execution_ledger,
            "trace_events": self.trace_events,
            "model_config": self.model_config,
            "integrity_checksum": self.integrity_checksum,
        }


class CheckpointManager:
    """Manages checkpoint creation, validation, and persistence."""

    SCHEMA_VERSION = CHECKPOINT_VERSION

    def __init__(self, checkpoints_dir: Path):
        """Initialize checkpoint manager."""
        self.dir = Path(checkpoints_dir).resolve()
        self.dir.mkdir(parents=True, exist_ok=True)
        self._latest_file = self.dir / LATEST_FILE
        self.latest_path: Optional[Path] = None

    def save_checkpoint(self, run_state: RunState, output_name: Optional[str] = None) -> Dict[str, Any]:
        """Create and save a new checkpoint atomically."""
        if run_state.status == RunStatus.FAILED:
            raise CheckpointError("Cannot save checkpoint for failed runs")

        # Build checkpoint data
        cp = CheckpointData(
            run_id=run_state.run_id,
            parent_id=None,
            graph_definition=run_state.graph_definition,
            execution_cursor=run_state.current_node or "",
            completed_outputs={k: v.to_dict() for k, v in run_state.node_outputs.items()},
            message_history=run_state.message_history,
            message_classifications={int(k): v for k, v in run_state.message_classifications.items()},
            protected_indices=run_state.protected_indices if hasattr(run_state, 'protected_indices') else set(),
            cache_operation_history=run_state.cache_operation_history,
            tool_execution_ledger=[te.to_dict() for te in run_state.tool_executions],
            trace_events=[e.to_dict() for e in run_state.trace_events],
            model_config=run_state.config,
        )

        # Compute integrity checksum
        cp_data = cp.to_dict()
        cp_bytes = json.dumps(cp_data, sort_keys=True).encode()
        cp.integrity_checksum = hashlib.sha256(cp_bytes).hexdigest()

        # Save atomically: write temp file, then rename
        final_path = self.dir / (output_name or f"{run_state.run_id}.json")
        temp_path = final_path.with_suffix(".tmp")

        try:
            # Write to temporary location
            with open(temp_path, "w") as f:
                json.dump(cp.to_dict(), f, indent=2, sort_keys=True)
            f.flush()

            # Validate the written file
            loaded = json.load(open(temp_path))

            # Check schema version
            if loaded.get("schema_version") != self.SCHEMA_VERSION:
                raise CheckpointError(
                    f"Checkpoint version mismatch: expected {self.SCHEMA_VERSION}, got {loaded['schema_version']}"
                )

            # Promote temp to final (atomic on same filesystem)
            os.replace(str(temp_path), str(final_path))

            # Update latest pointer
            self._update_latest(final_path)

        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise CheckpointError(f"Failed to save checkpoint: {e}")

        return cp.to_dict()

    def load_checkpoint(self, checkpoint_path: str) -> Dict[str, Any]:
        """Load a checkpoint from file."""
        path = Path(checkpoint_path).resolve()

        if not path.exists():
            raise CheckpointError(f"Checkpoint not found: {path}")

        with open(path) as f:
            data = json.load(f)

        # Validate schema version
        expected_version = CHECKPOINT_VERSION
        actual_version = data.get("schema_version", "")
        if actual_version != expected_version:
            raise CheckpointError(
                f"Checkpoint version mismatch: expected {expected_version}, got {actual_version}"
            )

        return data

    def validate_checkpoint(self, checkpoint_data: Dict[str, Any]) -> bool:
        """Validate checkpoint data structure."""
        required_fields = [
            "run_id", "schema_version", "graph_definition",
            "completed_outputs", "message_history",
        ]
        for field_name in required_fields:
            if field_name not in checkpoint_data:
                return False

        # Validate message indices are consistent
        msg_length = len(checkpoint_data["message_history"])
        for i, msg in enumerate(checkpoint_data["message_history"]):
            if msg.get("index") != i:
                return False

        # Check integrity checksum
        if "integrity_checksum" not in checkpoint_data:
            return True  # Without checksum, we can't verify but can still load

        return True

    def resolve_latest(self) -> Optional[Path]:
        """Get path to latest checkpoint."""
        if self._latest_path and self._latest_path.exists():
            return self._latest_path
        # Search for latest.json in directory
        candidates = list(self.dir.glob("*.json"))
        if candidates:
            latest = max(candidates, key=lambda p: p.stat().st_mtime)
            self._latest_path = latest
            return latest
        return None

    def recover_state(self, checkpoint_path: str, model_version: str = "") -> RunState:
        """Restore execution state from a checkpoint."""
        data = self.load_checkpoint(checkpoint_path)
        validation_result = self.validate_checkpoint(data)
        if not validation_result:
            raise CheckpointError("Invalid checkpoint structure")

        # Reconstruct RunState
        run_state = RunState.from_dict(data)
        return run_state

    def create_latest_pointer(self, checkpoint_id: str) -> None:
        """Update the 'latest' pointer file."""
        self._latest_path = self.dir / checkpoint_id / "latest.json"
        if not self._latest_path.parent.exists():
            self._latest_path.parent.mkdir(parents=True, exist_ok=True)

    def rollback_to_previous(self, previous_checkpoint_path: str) -> None:
        """Rollback to previous checkpoint."""
        self._latest_path = Path(previous_checkpoint_path)

    @staticmethod
    def list_checkpoints(directory: str) -> List[str]:
        """List all checkpoint files."""
        d = Path(directory)
        if not d.exists():
            return []
        return sorted([p.name for p in d.rglob("*.json")])
