"""Replay system for reproducing completed work without side effects."""

import hashlib
import json
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .state import RunState, RunStatus, ToolExecution


@dataclass
class ReusableResult:
    """A reusable result from a completed tool execution."""

    tool_name: str
    canonical_args: Dict[str, Any]
    output: Any
    execution_id: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_name": self.tool_name,
            "canonical_args": self.canonical_args,
            "output": self.output,
            "execution_id": self.execution_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReusableResult":
        """Create ReusableResult from dictionary."""
        return cls(
            tool_name=data["tool_name"],
            canonical_args=data["canonical_args"],
            output=data["output"],
            execution_id=data["execution_id"],
        )


def canonicalize(args: Dict[str, Any]) -> Dict[str, Any]:
    """Canonicalize tool arguments for comparison and deduplication."""
    # Sort keys and normalize values for deterministic representation
    if isinstance(args, dict):
        return {k: canonicalize(v) for k, v in sorted(args.items())}
    elif isinstance(args, list):
        return [canonicalize(item) for item in args]
    else:
        # Strings, numbers, booleans, None - return as-is
        return args


class ReplaySystem:
    """Replay system that preserves completed tool results."""

    def __init__(self, run_state: RunState):
        """Initialize replay system with run state."""
        self.run_state = run_state
        self.reusable: Dict[Tuple[str, Dict[str, Any]], ReusableResult] = {}
        self.seen: Set[str] = set()

    def preload_completed_results(self, additional_results: List[ReusableResult] = None) -> None:
        """Preload all completed tool results as reusable results."""
        for te in self.run_state.tool_executions:
            result = ReusableResult(
                tool_name=te.tool_name,
                canonical_args=canonicalize(te.arguments),
                output=te.output,
                execution_id=te.execution_id,
            )
            key = (result.tool_name, result.canonical_args)
            self.reusable[key] = result

    def get_result(self, tool_name: str, args: Dict[str, Any]) -> Optional[Any]:
        """Get a previously executed result for the same tool and arguments."""
        key = (tool_name, canonicalize(args))
        return self.reusable.get(key)

    def record_result(self, tool_name: str, args: Dict[str, Any], output: Any, execution_id: str) -> bool:
        """Record a result. Returns True if already known."""
        key = (tool_name, canonicalize(args))
        if key in self.reusable:
            return True
        self.reusable[key] = ReusableResult(
            tool_name=tool_name,
            canonical_args=canonicalize(args),
            output=output,
            execution_id=execution_id,
        )
        return False

    def is_duplicate(self, tool_name: str, args: Dict[str, Any], execution_id: str) -> bool:
        """Check if this tool call has been seen before."""
        key = (tool_name, canonicalize(args))
        if key in self.seen:
            return True
        self.seen.add(key)
        return False

    def available_results(self) -> int:
        """Count available reusable results."""
        return len(self.reusable)

    def duplicate_count(self) -> int:
        """Count how many duplicates were saved."""
        return sum(1 for i, te in enumerate(self.run_state.tool_executions) if i >= len(self.reusable))

    def reset(self) -> None:
        """Reset replay state."""
        self.reusable.clear()
        self.seen.clear()