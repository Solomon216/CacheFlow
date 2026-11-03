"""VulnTriage workflow builder — defines the 6-node DAG."""

from typing import Any, Dict, List, Callable, Tuple
from pathlib import Path

from cacheflow.dag import DAG, Node, NodeContract, Edge
from cacheflow.state import RunState, NodeOutput, ToolExecution, MessageClassification, RunStatus
from cacheflow.tools import RepositoryTools
from cacheflow.model_client import AKVModelClient, MockModelClient
from cacheflow.trace import TraceLogger, TraceEventType
from cacheflow.cache_plan import actions_for, plan_investigation_exit


def build_vuln_triage_graph(state: RunState, cfg) -> Tuple[List[Node], List[Edge]]:
    """Build the VulnTriage DAG: N0 ingest -> N1 repo_map -> N2 brief -> N3[*] investigate -> N4 cross_check -> N5 render"""
    tools = RepositoryTools(cfg.repo)

    nodes: List[Node] = []
    edges: List[Edge] = []

    # Contracts
    nodes.append(Node(
        node_id="N0",
        contract=NodeContract("N0", {"N1"}, {"repo", "advisories", "sorted_advisories"}),
        execute_fn=lambda dag, s: None,
        dependencies=[],
    ))
    nodes.append(Node(
        node_id="N1",
        contract=NodeContract("N1", {"N0"}, {"repo_index", "symbol_map", "briefing"}),
        execute_fn=lambda dag, s: None,
        dependencies=["N0"],
    ))
    nodes.append(Node(
        node_id="N2",
        contract=NodeContract("N2", {"N1"}, {"shared_history", "response"}),
        execute_fn=lambda dag, s: None,
        dependencies=["N1"],
    ))
    for i in range(3):  # fixed to first 3 for now; expand per advisory in Phase 6
        contract = NodeContract(f"N3[{i}]", {"N2"}, {"verdict", "evidence"})
        nodes.append(Node(
            node_id=f"N3[{i}]",
            contract=contract,
            execute_fn=lambda dag, s: None,
            dependencies=["N2"],
        ))
    nodes.append(Node(
        node_id="N4",
        contract=NodeContract("N4", {"N3[0]", "N3[1]", "N3[2]"}, {"all_verdicts", "cross_checked"}),
        execute_fn=lambda dag, s: None,
        dependencies=["N3[0]", "N3[1]", "N3[2]"],
    ))
    nodes.append(Node(
        node_id="N5",
        contract=NodeContract("N5", {"N4"}, {"report_json", "report_md"}),
        execute_fn=lambda dag, s: None,
        dependencies=["N4"],
    ))

    # Edges (deterministic ordering preserved)
    edges += [Edge("N0", "N1"), Edge("N1", "N2")]
    for i in range(3):
        edges.append(Edge("N2", f"N3[{i}]"))
    for i in range(3):
        edges.append(Edge(f"N3[{i}]", "N4"))
    edges.append(Edge("N4", "N5"))

    return nodes, edges


def main() -> None:
    """Expose workflow registration point."""
    from cacheflow.cli import register_workflow
    register_workflow("vulntriage", build_vuln_triage_graph)
    print("VulnTriage workflow registered.")


if __name__ == "__main__":
    main()
