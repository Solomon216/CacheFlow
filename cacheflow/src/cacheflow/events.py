"""Structured event logging for CacheFlow operations."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field


class EventType(str, Enum):
    """Types of traceable events."""

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
    """A single trace event in the execution log."""

    event_type: EventType
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
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
        """Create TraceEvent from dictionary."""
        return cls(
            event_type=EventType(data["event_type"]),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            sequence=data.get("sequence", 0),
            data=data,
        )


class TraceLogger:
    """Logger for structured JSONL trace events."""

    def __init__(self):
        """Initialize trace logger."""
        self.events: List[TraceEvent] = []
        self.current_seq: int = 0
        self.enabled: bool = True

    def log(self, event_type: EventType, data: Optional[Dict[str, Any]] = None) -> None:
        """Log an event."""
        if not self.enabled:
            return

        self.current_seq += 1
        event = TraceEvent(
            event_type=event_type,
            sequence=self.current_seq,
            data=data or {},
        )
        self.events.append(event)

    def log_structured(self, event_type: EventType, **kwargs) -> None:
        """Log an event with keyword arguments."""
        if not self.enabled:
            return

        self.current_seq += 1
        data = dict(kwargs)
        self.events.append(TraceEvent(
            event_type=event_type,
            sequence=self.current_seq,
            data=data,
        ))

    def get_events(self) -> List[Dict[str, Any]]:
        """Get all events as dictionaries."""
        return [e.to_dict() for e in self.events]

    def to_jsonl(self) -> str:
        """Serialize trace events to JSONL format."""
        lines = [json.dumps(event.to_dict(), indent=2) for event in self.events]
        return "\n".join(lines) + "\n"

    def save(self, path: str) -> None:
        """Save trace events to JSONL file."""
        with open(path, "w") as f:
            f.write(self.to_jsonl())

    def clear(self) -> None:
        """Clear all events."""
        self.events.clear()
        self.current_seq = 0

    def count(self) -> int:
        """Count total events logged."""
        return len(self.events)