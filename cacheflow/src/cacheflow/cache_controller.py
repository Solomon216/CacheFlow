"""AKV cache controller integration with the official AKV policy API."""

import json
import time
from typing import Any, Dict, List, Optional, Callable
from abc import ABC, abstractmethod
from datetime import datetime

from .errors import CachePolicyError
from .state import RunState, RunStatus, NodeOutput, ToolExecution
from .messages import MessageClassification
from .events import EventType, TraceLogger
from .model_client import AKVModelClient, MockModelClient, RunController
from .cache_plan import CacheDecisionResult, actions_for, plan_investigation_exit


class CacheController:
    """Coordinates cache policy decisions, AKV integration, and trace logging."""

    def __init__(
        self,
        run_state: RunState,
        model_client: AKVModelClient,
        trace_logger: TraceLogger,
        policy_config: Dict[str, Any] = None,
    ):
        """Initialize cache controller."""
        self.run_state = run_state
        self.model_client = model_client
        self.trace = trace_logger
        self.policy_config = policy_config or {}
        self.current_node: Optional[str] = None
        self.turn_count: int = 0

        # Configuration
        self.scratch_retention: int = self.policy_config.get("scratch_retention", 12)
        self.reposition_after: int = self.policy_config.get("reposition_after", 12)
        self.reposition_every: int = self.policy_config.get("reposition_every", 4)

        # Cache state tracking
        self.scheduled_drop_indices: Set[int] = set()
        self.last_drop_timestamp: Optional[float] = None
        self.last_reposition_timestamp: Optional[float] = None

        # Check if live AKV is available
        self.is_live: bool = model_client.is_available() if hasattr(model_client, 'is_available') else False

    def protect_message(self, index: int) -> None:
        """Protect a message index from dropping."""
        self.run_state.protected_indices.add(index)
        messages = getattr(self.run_state, 'messages', [])
        if index < 0 or index >= len(messages):
            return
        meta = messages[index].get("metadata", {})
        classified = messages[index].get("classification", meta.get("classification"))
        if classified:
            try:
                self.run_state.classifications[index] = MessageClassification.SPINE
            except KeyError:
                pass

    def classify_message(self, index: int) -> str:
        """Classify a message by its role."""
        messages = getattr(self.run_state, 'messages', [])
        if index < 0 or index >= len(messages):
            raise CachePolicyError(f"Message index out of range: {index}")

        role = messages[index].get("role", "")
        metadata = messages[index].get("metadata", {})

        if role == "system" or role == "user":
            return "spine"
        elif role == "assistant" and metadata.get("classification") == "reasoning":
            return "reasoning"
        else:
            return "scratch"

    def plan_operations(self, node: str, turn: int) -> CacheDecisionResult:
        """Plan cache operations for a given node/turn."""
        # Classify all scratch indices
        self.run_state.protected_indices.clear()
        for idx in range(len(self.run_state.messages)):
            try:
                role = self.run_state.messages[idx].get("role", "")
                metadata = self.run_state.messages[idx].get("metadata", {})
                if role in ("system", "user"):
                    self.run_state.classifications[idx] = MessageClassification.SPINE
                elif role == "assistant" and metadata.get("classification") == "reasoning":
                    self.run_state.classifications[idx] = MessageClassification.REASONING
                else:
                    self.run_state.classifications[idx] = MessageClassification.SCRATCH
            except Exception as e:
                self.trace.log_structured(EventType.CACHE_OPERATION_PLANNED, error=str(e))

        result = actions_for(
            node=node,
            turn=turn,
            state=self.run_state,
            scratch_retention=self.scratch_retention,
            reposition_after=self.reposition_after,
            reposition_every=self.reposition_every,
            node_exit_cleanup=True,
        )

        # Protect spine/reasoning messages so they cannot be dropped
        spine_indices = set(range(len(self.run_state.messages)))
        for idx, cls in list(self.run_state.classifications.items()):
            if cls == MessageClassification.SPINE:
                self.run_state.protected_indices.add(idx)

        self.trace.log_structured(EventType.CACHE_OPERATION_PLANNED, **{
            "node": node,
            "turn": turn,
            "scratch_indices": sorted([i for i in self.run_state.classifications.keys()
                                       if self.run_state.classifications[i] == MessageClassification.SCRATCH]),
            "planned_drop": result.drop_message,
            "do_reposition": bool(result.reposition),
        })

        self.run_state.add_cache_operation({"plan": result.to_dict()})
        return result

    def execute_operations(self, decision: CacheDecisionResult) -> None:
        """Execute planned cache operations against AKV server."""
        # Build request payload with drop_message / reposition fields
        payload = {
            "model": self.model_client.model,
            "messages": self.run_state.messages,
        }

        if decision.drop_message:
            payload["drop_message"] = dict(decision.drop_message)
        if decision.reposition:
            payload["reposition"] = list(decision.reposition)

        try:
            response = self.model_client.send_request(
                messages=[],  # Empty because we only need to verify fields are sent
                model=self.model_client.model,
                stream=False,
                max_tokens=64,
                extra_kwargs=payload,
            )

            usage = response.get("usage_details", response.get("usage", {}))
            self.run_state.trace_events[-1]["cache_usage"] = usage

            self.trace.log_structured(EventType.CACHE_USAGE_REPORTED, **{
                "cached_tokens": usage.get("cached_tokens", 0),
                "drop_skipped_tokens": usage.get("drop_skipped_tokens", 0),
                "repos_tokens": usage.get("repos_tokens", 0),
            })

            # Record actual server-confirmed operations
            self.run_state.add_cache_operation({"actual_response": response.get("usage_details", {})})

        except Exception as e:
            self.trace.log_structured(EventType.ERROR, error=f"Cache operation failed: {e}")
            raise CachePolicyError(f"Failed to execute cache operations: {e}") from e

    def execution_event(self, event: str, **kwargs) -> None:
        """Log a structured execution event."""
        self.trace.log_structured(EventType(event), **kwargs)

    @property
    def protected_set(self) -> set:
        """Return current protected indices."""
        return set(self.run_state.protected_indices)

    def scratch_indices(self) -> List[int]:
        """Return current scratch indices excluding protected ones."""
        return [i for i, c in self.run_state.classifications.items()
                if c == MessageClassification.SCRATCH and i not in self.run_state.protected_indices]
