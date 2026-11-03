"""CacheFlow exception hierarchy."""


class CacheFlowError(Exception):
    """Base exception for all CacheFlow errors."""


class DAGError(CacheFlowError):
    """Raised for graph definition or execution errors."""


class InvalidGraphError(DAGError):
    """Raised when graph definition is invalid (cycles, bad edges, bad contracts)."""


class NodeInputOutputError(DAGError):
    """Raised when node input/output contracts are violated."""


class InvalidMessageIndexError(CacheFlowError):
    """Raised when message indices are out of bounds or invalid."""


class CachePolicyError(CacheFlowError):
    """Raised when cache policy decisions cannot be applied safely."""


class CheckpointError(CacheFlowError):
    """Raised when checkpoint operations fail or are incompatible."""


class ModelClientError(CacheFlowError):
    """Raised when model/AKV communication fails."""


class ToolExecutionError(CacheFlowError):
    """Raised when tool execution fails or is rejected."""


class ValidationError(CacheFlowError):
    """Raised when data validation fails."""