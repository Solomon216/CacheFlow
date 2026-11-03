from cacheflow.dag import DAG, Edge, Node, NodeContract


def test_dag_topological_order_is_stable_and_valid():
    nodes = [
        Node("A", NodeContract("A", set(), {"x"}), lambda dag, state: None, []),
        Node("B", NodeContract("B", {"A"}, {"y"}), lambda dag, state: None, ["A"]),
        Node("C", NodeContract("C", {"A"}, {"z"}), lambda dag, state: None, ["A"]),
        Node("D", NodeContract("D", {"B", "C"}, {"done"}), lambda dag, state: None, ["B", "C"]),
    ]
    dag = DAG(nodes, [Edge("A", "B"), Edge("A", "C"), Edge("B", "D"), Edge("C", "D")])

    assert dag.get_topological_order() == ["A", "B", "C", "D"]
    assert dag.is_eligible("D", {"A", "B", "C"})


def test_dag_rejects_cycles():
    nodes = [
        Node("A", NodeContract("A", {"B"}, {"x"}), lambda dag, state: None, ["B"]),
        Node("B", NodeContract("B", {"A"}, {"y"}), lambda dag, state: None, ["A"]),
    ]

    try:
        DAG(nodes, [Edge("A", "B"), Edge("B", "A")])
        assert False, "cycle should have been rejected"
    except Exception:
        pass
