"""DAG engine for deterministic workflow execution."""

from typing import Any, Dict, List, Set, Tuple, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from collections import defaultdict, deque
from abc import ABC, abstractmethod
import hashlib
import json

from .errors import InvalidGraphError, NodeInputOutputError, DAGError
from .state import NodeStatus, RunState, RunStatus


T = TypeVar('T')


@dataclass(frozen=True)
class NodeContract:
    """Contract for a DAG node's inputs and outputs."""

    node_id: str
    inputs: Set[str]
    outputs: Set[str]

    def __post_init__(self):
        if not self.node_id or not isinstance(self.node_id, str):
            raise ValueError("Node ID must be a non-empty string")
        if not isinstance(self.inputs, set):
            raise ValueError("Inputs must be a set")
        if not isinstance(self.outputs, set):
            raise ValueError("Outputs must be a set")


@dataclass(frozen=True)
class Edge:
    """Directed edge between nodes."""

    from_node: str
    to_node: str

    def __post_init__(self):
        if not self.from_node or not self.to_node:
            raise ValueError("Edge must have both from_node and to_node")


@dataclass
class Node:
    """DAG node definition."""

    node_id: str
    contract: NodeContract
    execute_fn: Callable[["DAG", "RunState"], Any]
    dependencies: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.node_id or not isinstance(self.node_id, str):
            raise ValueError("Node ID must be a non-empty string")
        if not callable(self.execute_fn):
            raise ValueError("Execute function must be callable")


class DAG:
    """Deterministic DAG with validated execution order."""

    def __init__(self, nodes: List[Node], edges: List[Edge]):
        """Initialize DAG with nodes and edges."""
        self.nodes: Dict[str, Node] = {n.node_id: n for n in nodes}
        self.edges: List[Edge] = edges
        self._adjacency: Dict[str, List[str]] = defaultdict(list)
        self._reverse_adjacency: Dict[str, List[str]] = defaultdict(list)
        self._topological_order: Optional[List[str]] = None

        self._build_adjacency()
        self._validate()

    def _build_adjacency(self) -> None:
        """Build adjacency lists from edges."""
        self._adjacency.clear()
        self._reverse_adjacency.clear()
        for edge in self.edges:
            self._adjacency[edge.from_node].append(edge.to_node)
            self._reverse_adjacency[edge.to_node].append(edge.from_node)

    def _validate(self) -> None:
        """Validate DAG structure."""
        # Check all referenced nodes exist
        all_node_ids = set(self.nodes.keys())
        for edge in self.edges:
            if edge.from_node not in all_node_ids:
                raise InvalidGraphError(f"Edge references unknown node: {edge.from_node}")
            if edge.to_node not in all_node_ids:
                raise InvalidGraphError(f"Edge references unknown node: {edge.to_node}")

        # Check for cycles
        if self._has_cycle():
            raise InvalidGraphError("DAG contains cycles")

        # Validate node contracts
        for node in self.nodes.values():
            self._validate_node_contract(node)

    def _has_cycle(self) -> bool:
        """Check for cycles using DFS."""
        visited = set()
        rec_stack = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            for neighbor in self._adjacency[node_id]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node_id)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True
        return False

    def _validate_node_contract(self, node: Node) -> None:
        """Validate node contract against DAG."""
        # Check that declared dependencies match actual edges
        actual_deps = set(self._reverse_adjacency[node.node_id])
        declared_deps = set(node.dependencies)
        if actual_deps != declared_deps:
            raise InvalidGraphError(
                f"Node {node.node_id} dependencies mismatch: "
                f"declared={declared_deps}, actual={actual_deps}"
            )

    def get_topological_order(self) -> List[str]:
        """Get stable topological ordering of nodes."""
        if self._topological_order is not None:
            return self._topological_order

        # Kahn's algorithm with stable sorting
        in_degree: Dict[str, int] = {n: 0 for n in self.nodes}
        for edge in self.edges:
            in_degree[edge.to_node] += 1

        # Use deque for stable ordering
        queue = deque(sorted([n for n, d in in_degree.items() if d == 0]))
        order = []

        while queue:
            node_id = queue.popleft()
            order.append(node_id)

            for neighbor in sorted(self._adjacency[node_id]):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(self.nodes):
            raise InvalidGraphError("Failed to compute topological order (cycle detected)")

        self._topological_order = order
        return order

    def get_dependencies(self, node_id: str) -> List[str]:
        """Get direct dependencies of a node."""
        return sorted(self._reverse_adjacency[node_id])

    def get_dependents(self, node_id: str) -> List[str]:
        """Get direct dependents of a node."""
        return sorted(self._adjacency[node_id])

    def is_eligible(self, node_id: str, completed: Set[str]) -> bool:
        """Check if a node is eligible to execute."""
        deps = self.get_dependencies(node_id)
        return all(dep in completed for dep in deps)

    def get_execution_plan(self) -> List[str]:
        """Get the full execution plan in order."""
        return self.get_topological_order()

    def execute(
        self,
        state: "RunState",
        node_executor: Callable[["DAG", "RunState", str], Any],
    ) -> Any:
        """Execute the DAG using the provided executor function."""
        completed = set(state.completed_nodes)
        order = self.get_topological_order()

        for node_id in order:
            if node_id in completed:
                continue

            if not self.is_eligible(node_id, completed):
                raise DAGError(f"Node {node_id} is not eligible for execution")

            state.current_node = node_id
            state.update_status(RunStatus.RUNNING)

            try:
                result = node_executor(self, state, node_id)
                completed.add(node_id)
                state.completed_nodes.append(node_id)
            except Exception as e:
                state.failed_nodes.append(node_id)
                state.update_status(RunStatus.FAILED)
                raise DAGError(f"Node {node_id} failed: {e}") from e

        state.update_status(RunStatus.COMPLETED)
        return state

    def get_graph_hash(self) -> str:
        """Compute stable hash of graph definition."""
        graph_def = self.to_dict()
        return hashlib.sha256(json.dumps(graph_def, sort_keys=True).encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert DAG to dictionary."""
        return {
            "nodes": {
                node_id: {
                    "node_id": node.node_id,
                    "contract": {
                        "node_id": node.contract.node_id,
                        "inputs": sorted(node.contract.inputs),
                        "outputs": sorted(node.contract.outputs),
                    },
                    "dependencies": sorted(node.dependencies),
                }
                for node_id, node in self.nodes.items()
            },
            "edges": [
                {"from": e.from_node, "to": e.to_node}
                for e in self.edges
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], node_executors: Dict[str, Callable]) -> "DAG":
        """Create DAG from dictionary."""
        nodes = []
        for node_id, node_data in data.get("nodes", {}).items():
            contract_data = node_data["contract"]
            contract = NodeContract(
                node_id=contract_data["node_id"],
                inputs=set(contract_data["inputs"]),
                outputs=set(contract_data["outputs"]),
            )
            execute_fn = node_executors.get(node_id)
            if not execute_fn:
                raise DAGError(f"No executor found for node: {node_id}")
            nodes.append(Node(
                node_id=node_id,
                contract=contract,
                execute_fn=execute_fn,
                dependencies=node_data.get("dependencies", []),
            ))

        edges = [Edge(e["from"], e["to"]) for e in data.get("edges", [])]
        return cls(nodes, edges)


class NodeExecutor(ABC):
    """Abstract base for node executors."""

    @abstractmethod
    def execute(self, dag: DAG, state: "RunState", node_id: str) -> Any:
        """Execute a node."""
        pass