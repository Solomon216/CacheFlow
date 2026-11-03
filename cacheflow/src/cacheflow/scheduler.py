"""Stable topological scheduler for CacheFlow."""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from collections import deque
import time

from .dag import DAG
from .state import RunState, NodeStatus, NodeOutput
from .errors import DAGError


@dataclass
class ScheduledNode:
    """Scheduled node with metadata."""

    node_id: str
    dependencies_met: bool
    attempt_number: int = 0

    def reset(self):
        """Reset attempt number for retry."""
        self.attempt_number = 0


class TopologicalScheduler:
    """Stable topological scheduler that respects DAG ordering."""

    def __init__(self, dag: DAG, max_attempts: int = 3):
        """Initialize scheduler with DAG configuration."""
        self.dag = dag
        self.max_attempts = max_attempts
        self.scheduled: Dict[str, ScheduledNode] = {}
        self._completed: Set[str] = set()
        self._failed: Set[str] = set()

    def schedule_all(self) -> List[str]:
        """Schedule all eligible nodes in stable order."""
        order = self.dag.get_topological_order()
        scheduled_order = []

        # Track which nodes are eligible based on completed dependencies
        for node_id in order:
            deps = self.dag.get_dependencies(node_id)
            deps_met = all(dep in self._completed for dep in deps)

            if deps_met and node_id not in self._failed:
                self.scheduled[node_id] = ScheduledNode(
                    node_id=node_id,
                    dependencies_met=True,
                    attempt_number=0,
                )
                scheduled_order.append(node_id)
            else:
                # For failed nodes, still mark but won't retry in this pass
                self.scheduled[node_id] = ScheduledNode(
                    node_id=node_id,
                    dependencies_met=False,
                    attempt_number=len(self._failed),
                )

        return scheduled_order

    def mark_completed(self, node_id: str) -> None:
        """Mark a node as completed."""
        self._completed.add(node_id)
        if node_id in self.scheduled:
            self.scheduled[node_id].reset()

    def mark_failed(self, node_id: str) -> None:
        """Mark a node as failed."""
        self._failed.add(node_id)
        if node_id in self.scheduled:
            self.scheduled[node_id].attempt_number += 1

    def get_ready_nodes(self) -> List[str]:
        """Get nodes ready to execute (no unmet dependencies)."""
        ready = []
        for node_id, scheduled in self.scheduled.items():
            if node_id in self._completed or node_id in self._failed:
                continue
            deps = self.dag.get_dependencies(node_id)
            if all(dep in self._completed for dep in deps):
                ready.append(node_id)
        return sorted(ready)

    def get_next_execution_batch(self, count: int = 1) -> List[str]:
        """Get the next batch of nodes to execute (sorted for determinism)."""
        available = self.get_ready_nodes()
        return available[:count] if available else []

    def should_retry(self, node_id: str) -> bool:
        """Check if a node should be retried."""
        scheduled = self.scheduled.get(node_id)
        if not scheduled or scheduled.attempt_number >= self.max_attempts:
            return False
        return True

    def reset(self) -> None:
        """Reset all scheduling state."""
        self._completed.clear()
        self._failed.clear()
        self.scheduled.clear()
