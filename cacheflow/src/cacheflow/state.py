"""Execution state models for CacheFlow."""

import json
import hashlib
from typing import Any, Dict, List, Set, Optional, Literal
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .errors import CacheFlowError
from .messages import MessageClassification


class RunStatus(str, Enum):
    """Status of a run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    RESUMED = "resumed"


class NodeStatus(str, Enum):
    """Status of a node execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class NodeOutput:
    """Output from a node execution."""

    node_id: str
    status: NodeStatus
    outputs: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert NodeOutput to dictionary."""
        return {
            "node_id": self.node_id,
            "status": self.status.value,
            "outputs": self.outputs,
            "timestamp": self.timestamp.isoformat(),
            "retry_count": self.retry_count,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeOutput":
        """Create NodeOutput from dictionary."""
        return cls(
            node_id=data["node_id"],
            status=NodeStatus(data["status"]),
            outputs=data["outputs"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            retry_count=data.get("retry_count", 0),
            error=data.get("error"),
        )


@dataclass
class ToolExecution:
    """Record of a tool execution."""

    execution_id: str
    tool_name: str
    arguments: Dict[str, Any]
    output: Any
    status: Literal["success", "failed", "timeout"]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None
    node_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert ToolExecution to dictionary."""
        return {
            "execution_id": self.execution_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "output": self.output,
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
            "node_id": self.node_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolExecution":
        """Create ToolExecution from dictionary."""
        return cls(
            execution_id=data["execution_id"],
            tool_name=data["tool_name"],
            arguments=data["arguments"],
            output=data["output"],
            status=data["status"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            error=data.get("error"),
            node_id=data.get("node_id"),
        )


class RunState(BaseModel):
    """Complete execution state for a CacheFlow run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., description="Unique identifier for this run")
    workflow: str = Field(..., description="Workflow being executed")
    status: RunStatus = Field(RunStatus.PENDING, description="Current run status")
    start_time: Optional[datetime] = Field(None, description="Run start timestamp")
    end_time: Optional[datetime] = Field(None, description="Run end timestamp")
    current_node: Optional[str] = Field(None, description="Currently executing node")
    completed_nodes: List[str] = Field(default_factory=list, description="List of completed nodes")
    failed_nodes: List[str] = Field(default_factory=list, description="List of failed nodes")
    retried_nodes: List[str] = Field(default_factory=list, description="List of retried nodes")
    tool_executions: List[ToolExecution] = Field(default_factory=list, description="All tool executions")
    node_outputs: Dict[str, NodeOutput] = Field(default_factory=dict, description="Node outputs")
    message_history: List[Dict[str, Any]] = Field(default_factory=list, description="Complete message history")
    cache_operation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Cache operation history")
    graph_definition: Dict[str, Any] = Field(default_factory=dict, description="Graph definition")
    config: Dict[str, Any] = Field(default_factory=dict, description="Run configuration")
    trace_events: List[Dict[str, Any]] = Field(default_factory=list, description="Trace events")
    checkpoint_version: str = Field("1.0", description="Checkpoint schema version")
    event_sequence: int = Field(0, description="Current event sequence number")
    protected_indices: List[int] = Field(default_factory=list, description="Protected message indices")
    message_classifications: Dict[int, str] = Field(default_factory=dict, description="Message index classification")

    @field_validator("run_id")
    @classmethod
    def validate_run_id(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Run ID must be a non-empty string")
        return v

    @field_validator("workflow")
    @classmethod
    def validate_workflow(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Workflow name must be a non-empty string")
        return v

    def protected_set(self) -> set[int]:
        """Return the current set of protected indices (for cache-policy use)."""
        return set(self.protected_indices)

    def protect_index(self, index: int) -> None:
        """Protect a message index so AKV never drops it."""
        if index < len(self.message_history) and index >= 0:
            if index not in self.protected_indices:
                self.protected_indices.append(index)
            self.message_classifications[index] = MessageClassification.SPINE.value

    def to_dict(self) -> Dict[str, Any]:
        """Convert RunState to dictionary."""
        return {
            "run_id": self.run_id,
            "workflow": self.workflow,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "current_node": self.current_node,
            "completed_nodes": list(self.completed_nodes),
            "failed_nodes": list(self.failed_nodes),
            "retried_nodes": list(self.retried_nodes),
            "tool_executions": [te.to_dict() for te in self.tool_executions],
            "node_outputs": {k: v.to_dict() for k, v in self.node_outputs.items()},
            "message_history": list(self.message_history),
            "cache_operation_history": list(self.cache_operation_history),
            "graph_definition": self.graph_definition,
            "config": self.config,
            "trace_events": list(self.trace_events),
            "checkpoint_version": self.checkpoint_version,
            "event_sequence": self.event_sequence,
            "protected_indices": sorted(self.protected_indices),
            "message_classifications": {k: v for k, v in self.message_classifications.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RunState":
        """Create RunState from dictionary."""
        # Convert tool executions back to ToolExecution objects
        tool_executions = []
        for te_data in data.get("tool_executions", []):
            tool_executions.append(ToolExecution.from_dict(te_data))

        # Convert node outputs back to NodeOutput objects
        node_outputs = {}
        for node_id, output_data in data.get("node_outputs", {}).items():
            node_outputs[node_id] = NodeOutput.from_dict(output_data)

        msg_history = data.get("message_history", [])
        prot = sorted({int(v) for v in data.get("protected_indices", [])})
        cls_map = {int(k): str(v) for k, v in data.get("message_classifications", {}).items()}

        return cls(
            run_id=data["run_id"],
            workflow=data["workflow"],
            status=RunStatus(data["status"]),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None,
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            current_node=data.get("current_node"),
            completed_nodes=data.get("completed_nodes", []),
            failed_nodes=data.get("failed_nodes", []),
            retried_nodes=data.get("retried_nodes", []),
            tool_executions=tool_executions,
            node_outputs=node_outputs,
            message_history=msg_history,
            cache_operation_history=data.get("cache_operation_history", []),
            graph_definition=data.get("graph_definition", {}),
            config=data.get("config", {}),
            trace_events=data.get("trace_events", []),
            checkpoint_version=data.get("checkpoint_version", "1.0"),
            event_sequence=data.get("event_sequence", 0),
            protected_indices=prot,
            message_classifications=cls_map,
        )

    def add_tool_execution(self, tool_execution: ToolExecution) -> None:
        """Add a tool execution to the state."""
        self.tool_executions.append(tool_execution)
        self.event_sequence += 1

    def add_node_output(self, node_output: NodeOutput) -> None:
        """Add a node output to the state."""
        self.node_outputs[node_output.node_id] = node_output
        self.event_sequence += 1

    def add_message(self, message: Dict[str, Any]) -> None:
        """Add a message to the message history."""
        self.message_history.append(message)
        idx = len(self.message_history) - 1
        meta = message.get("metadata", {})
        classification = meta.get("classification")
        role = message.get("role", "")

        if classification:
            self.message_classifications[idx] = str(classification)
        elif role == "assistant":
            self.message_classifications[idx] = MessageClassification.SCRATCH.value
        elif role in ("system", "user"):
            self.message_classifications[idx] = MessageClassification.SPINE.value

        if role in ("system", "user"):
            self.message_classifications[idx] = MessageClassification.SPINE.value
            if idx not in self.protected_indices:
                self.protected_indices.append(idx)
        elif role == "assistant" and meta.get("classification") == "reasoning":
            self.message_classifications[idx] = MessageClassification.REASONING.value
            if idx not in self.protected_indices:
                self.protected_indices.append(idx)

    def classify_all(self) -> None:
        """Re-derive all classifications from message roles (used before cache planning)."""
        protected: set[int] = set()
        for i, msg in enumerate(self.message_history):
            role = msg.get("role", "")
            meta = msg.get("metadata", {})
            if role in ("system", "user"):
                self.message_classifications[i] = MessageClassification.SPINE.value
                protected.add(i)
            elif role == "assistant" and meta.get("classification") == "reasoning":
                self.message_classifications[i] = MessageClassification.REASONING.value
                protected.add(i)
            else:
                self.message_classifications[i] = MessageClassification.SCRATCH.value
        self.protected_indices = sorted(protected)

    def scratch_indices(self) -> List[int]:
        """Return scratch indices (excluding protected)."""
        scratch = []
        for i, cls in self.message_classifications.items():
            if cls == MessageClassification.SCRATCH.value and i not in self.protected_indices:
                scratch.append(i)
        return sorted(scratch)

    def update_status(self, new_status: RunStatus, timestamp: Optional[datetime] = None) -> None:
        """Update the run status."""
        self.status = new_status
        if timestamp:
            if new_status == RunStatus.PENDING:
                self.start_time = timestamp
            elif new_status in (RunStatus.COMPLETED, RunStatus.FAILED):
                self.end_time = timestamp
        self.event_sequence += 1

    def can_resume(self) -> bool:
        """Check if the run can be resumed from current state."""
        return (
            self.status in (RunStatus.PAUSED, RunStatus.FAILED) and
            self.completed_nodes and
            not self.failed_nodes
        ) or (
            self.status == RunStatus.RUNNING and
            self.current_node
        )
