"""Structured trace logger for CacheFlow events."""

import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path


class TraceEventType(str, Enum):
    """Types of structured traceable events."""

    RUN_CREATED = "run_created"
    GRAPH_CONSTRUCTED = "graph_constructed"
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"
    TOOL_REQUESTED = "tool_requested"
    TOOL_EXECUTED = "tool_executed"
    MODEL_REQUEST_SENT = "model_request_sent"
    MODEL_RESPONSE_RECEIVED = "model_response_received"
    CACHE_OPERATION_PLANNED = "cache_operation_planned"
    CACHE_OPERATION_SENT = "cache_operation_sent"
    CACHE_USAGE_REPORTED = "cache_usage_reported"
    CHECKPOINT_COMMITTED = "checkpoint_committed"
    RESUME_ATTEMPTED = "resume_attempted"
    RESUME_SUCCESSFUL = "resume_successful"
    RESUME_FAILED = "resume_failed"
    FINAL_REPORT_CREATED = "final_report_created"
    ERROR = "error"


@dataclass
class TraceEvent:
    """A single trace event with full schema information."""

    event_type: TraceEventType
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sequence: int = 0
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "sequence": self.sequence,
            **self.data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraceEvent":
        """Create from dictionary."""
        return cls(
            event_type=TraceEventType(data["event_type"]),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            sequence=data.get("sequence", 0),
            data=data,
        )


class TraceLogger:
    """Logger that writes JSONL events with versioned schema."""

    SCHEMA_VERSION = "1.0"

    def __init__(self, output_path: Optional[Path] = None, enabled: bool = True):
        """Initialize trace logger."""
        self.events: List[TraceEvent] = []
        self.current_seq: int = 0
        self.output_path = output_path or None
        self.enabled = enabled

    def log(self, event_type: TraceEventType, **kwargs) -> None:
        """Log a structured event."""
        if not self.enabled:
            return
        self.current_seq += 1
        self.events.append(TraceEvent(
            event_type=event_type,
            sequence=self.current_seq,
            data=kwargs,
        ))

    def save(self, path: str) -> None:
        """Save trace events as JSONL file."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as f:
            for event in self.events:
                f.write(json.dumps(event.to_dict(), indent=2) + "\n")

    def append_jsonl(self, line: str) -> None:
        """Append a single line of JSON to the trace file."""
        with open(self.output_path, "a") as f:
            f.write(line + "\n")

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all events as dictionaries."""
        return [e.to_dict() for e in self.events]

    def count(self) -> int:
        """Return number of events logged."""
        return len(self.events)

    def clear(self) -> None:
        """Clear all events."""
        self.events = []
        self.current_seq = 0

    def summarize(self) -> Dict[str, Any]:
        """Produce a summary statistics dict."""
        summary = {
            "schema_version": self.SCHEMA_VERSION,
            "total_events": self.count(),
            "events_by_type": {},
            "first_event": self.events[0].to_dict() if self.events else None,
            "last_event": self.events[-1].to_dict() if self.events else None,
        }
        for e in self.events:
            et = e.event_type.value
            summary["events_by_type"][et] = summary["events_by_type"].get(et, 0) + 1
        return summary
