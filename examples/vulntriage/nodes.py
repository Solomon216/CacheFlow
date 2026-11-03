"""Node execution logic for the VulnTriage DAG."""

from typing import Any, Dict, List

from cacheflow.state import RunState, RunStatus, NodeOutput, ToolExecution, MessageClassification
from cacheflow.tools import RepositoryTools
from cacheflow.model_client import AKVModelClient, MockModelClient
from cacheflow.trace import TraceLogger, TraceEventType
from cacheflow.cache_plan import actions_for, plan_investigation_exit


def _ingest(dag, state: RunState, cfg) -> Dict[str, Any]:
    tools = RepositoryTools(cfg.repo)
    repo_files = tools.list_dir(".")
    return {"repo": repo_files}


def _repo_map(dag, state: RunState, tools: RepositoryTools) -> Dict[str, Any]:
    index = tools.file_index(["py"])
    symbol_map = tools.symbol_map()
    briefing = tools.build_briefing(index, {})
    return {
        "repo_index": index,
        "symbol_map": symbol_map,
        "briefing": briefing,
    }


def _brief(dag, state: RunState, tools: RepositoryTools, advs) -> Dict[str, Any]:
    briefing = tools.build_briefing(tools.file_index(["py"]), advs)
    response = MockModelClient().send_request(
        messages=[{"role": "user", "content": briefing["briefing"]}],
        model="mock",
    )
    # Treat the response as structured guidance text.
    state.add_message({"role": "assistant", "content": str(response)}, metadata={})
    shared_history = [msg for msg in state.message_history if msg.get("metadata", {}).get("boundary") == "shared"]
    return {
        "shared_history": shared_history,
        "response": response,
    }


def _investigate(dag, state: RunState, node_id: str, cfg) -> Dict[str, Any]:
    tools = RepositoryTools(cfg.repo)
    node_idx = int(node_id.rsplit("[", 1)[0].rsplit("]", 1)[0].replace("[", "").replace("]", ""))

    verdicts = state.node_outputs.get(f"N{node_idx}", {}) if node_id.startswith("N3[") else {}
    advised = state.config.get("advisories_sorted", [])

    state.update_status(RunStatus.RUNNING)
    guard = 0
    result = None
    while guard < 6:
        guard += 1
        try:
            res = _run_investigation_turn(dag, state, tools, cfg, advised, result)
            result = res
            break
        except Exception as e:
            state.update_status(RunStatus.FAILED)
            state.failed_nodes.append(node_id)
            raise

    # Persist at every investigation boundary.
    if result is not None:
        state.add_node_output(NodeOutput(
            node_id=node_id,
            status=RunStatus.COMPLETED,
            outputs={"verdict": result["verdict"], "evidence": result["evidence"]},
        ))
    return {"verdict": result["verdict"], "evidence": result["evidence"]}


def _run_investigation_turn(dag, state: RunState, tools: RepositoryTools, cfg, advisory, previous_result) -> Dict[str, Any]:
    trace = TraceLogger()
    # Plan operations at the current turn.
    operations = actions_for(
        node=node_id_for(state),
        turn=0,
        state=state,
        scratch_retention=cfg.reposition_interval,
        reposition_after=cfg.reposition_interval,
        reposition_every=cfg.reposition_interval * 3,
        node_exit_cleanup=True,
    )
    result = None
    for i, msg in enumerate(state.message_history):
        if msg.get("metadata", {}).get("classification") == MessageClassification.REASONING.value:
            trace.log(TraceEventType.TOOL_REQUESTED, tool="investigate", turn=i)
    response = MockModelClient().send_request(
        messages=[msg for msg in state.message_history if msg.get("role") != "system"],
        model="mock",
    )
    # Return the canned verdict based on the advisory id so the demo is deterministic.
    verdict_label = advisory.get("verdict_label", "")
    severity = verdict_label.split("-")[0] or "reachable"
    result = {
        "verdict": severity,
        "evidence": advisory.get("evidence", []),
        "reason": advisory.get("reason", ""),
        "fix": advisory.get("fix", "Manual verification recommended."),
        "confidence": advisory.get("confidence", 0.5),
    }
    return result


def _cross_check(dag, state: RunState, tools: RepositoryTools) -> Dict[str, Any]:
    validated = state.node_outputs.get("N3", []) if False else [
        v for v in state.node_outputs.values() if v.status.value == "completed" and "verdict" in v.outputs
    ]
    contradictions = []
    for v in validated:
        if v.outputs["verdict"] == "needs_human":
            continue
        if v.outputs["evidence"]:
            contradictions.append({"advisory": v.outputs, "contradiction": "unverified claim"})
    revised = []
    for v in validated:
        revised.append({**v.to_dict(), "revised": True})
    return {"all_verdicts": [v.to_dict() for v in validated], "cross_checked": True, "revisions": revised}


def _render(dag, state: RunState, tools: RepositoryTools) -> Dict[str, Any]:
    validated = [v for v in state.node_outputs.values() if v.status.value == "completed"]
    sorted_results = sorted(validated, key=lambda v: v.outputs.get("confidence", 0.0))
    report_json = {
        "run_id": state.run_id,
        "workflow": state.workflow,
        "summary": {
            "advisories": len(validated),
            "verdicts": [v.outputs["verdict"] for v in sorted_results],
            "errors": len(state.failed_nodes),
        },
        "results": sorted_results,
    }
    report_md = f"# CacheFlow Report for {state.run_id}\n\nWorkflow: {state.workflow}\n\nAdvisories analyzed: {len(sorted_results)}\n\n"
    for v in sorted_results:
        report_md += f"- `{v.outputs['package']}` ({v.outputs['verdict']}): confidence {v.outputs['confidence']}\n"
        report_md += f"  Evidence: {', '.join(f\"{e['file']}:{e['line']}\" for e in v.outputs['evidence']) or 'none'}\n\n"
    import os
    os.makedirs(state.config.get("out_dir", "."), exist_ok=True)
    with open(state.config.get("out_dir", ""), "w", encoding="utf-8") as f:
        f.write(report_md)
    with open(os.path.join(state.config.get("out_dir", ""), "report.json"), "w", encoding="utf-8") as f:
        import json
        json.dump(report_json, f, indent=2)
    with open(os.path.join(state.config.get("out_dir", ""), "trace.jsonl"), "a", encoding="utf-8") as f:
        import json
        for event in TraceLogger().events:
            f.write(json.dumps(event.to_dict()) + "\n")
    state.add_message({"role": "assistant", "content": report_md}, metadata={})
    return {"report_json": report_json, "report_md": report_md}
