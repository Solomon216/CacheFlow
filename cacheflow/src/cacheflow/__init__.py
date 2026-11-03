"""CacheFlow — deterministic agent execution runtime with AKV KV-cache management."""

from .dag import DAG, DAGError, Node, NodeContract, Edge
from .state import RunState, RunStatus, NodeStatus, NodeOutput, ToolExecution
from .messages import AppendOnlyMessageHistory, MessageClassification
from .cache_controller import CacheController, CacheDecisionResult
from .checkpoints import CheckpointManager
from .trace import TraceLogger, TraceEvent, TraceEventType
from .errors import CacheFlowError
from .config import RunConfig

__version__ = "0.1.0"

WORKFLOWS: dict[str, object] = {}


def register_workflow(name: str, builder) -> None:
    """Register a workflow builder in the top-level package namespace."""
    WORKFLOWS[name] = builder


try:
    from .examples.vulntriage.workflow import build_vuln_triage_graph
except Exception:  # pragma: no cover - package-initialization resilience
    build_vuln_triage_graph = None

if build_vuln_triage_graph is not None:
    register_workflow("vulntriage", build_vuln_triage_graph)

__all__ = [
    "DAG",
    "DAGError",
    "RunState",
    "RunStatus",
    "NodeStatus",
    "NodeOutput",
    "ToolExecution",
    "AppendOnlyMessageHistory",
    "MessageClassification",
    "CacheController",
    "CacheDecisionResult",
    "CheckpointManager",
    "TraceLogger",
    "TraceEvent",
    "TraceEventType",
    "CacheFlowError",
    "RunConfig",
    "WORKFLOWS",
    "register_workflow",
    "build_vuln_triage_graph",
    "__version__",
]
