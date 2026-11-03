"""Cache policy planning — pure, unit-testable policy logic."""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field

from .errors import CachePolicyError
from .state import RunState
from .messages import MessageClassification


@dataclass
class CacheAction:
    """A single cache operation decision."""

    decision_type: str  # drop | reposition | protect
    indices: List[int]
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    node_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decision_type": self.decision_type,
            "indices": sorted(self.indices),
            "reason": self.reason,
            "timestamp": self.timestamp,
            "node_id": self.node_id,
        }


@dataclass
class CacheDecisionResult:
    """Result of processing a cache decision through AKV."""

    drop_message: Dict[int, List[int]] = field(default_factory=dict)
    reposition: List[int] = field(default_factory=list)
    policy_version: str = "1.0"
    cached_tokens: int = 0
    drop_skipped_tokens: int = 0
    repos_tokens: int = 0
    historical_prefix_digest: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "drop_message": self.drop_message,
            "reposition": list(self.reposition),
            "policy_version": self.policy_version,
            "cached_tokens": self.cached_tokens,
            "drop_skipped_tokens": self.drop_skipped_tokens,
            "repos_tokens": self.repos_tokens,
            "historical_prefix_digest": self.historical_prefix_digest,
        }


def _scratch_indices(state: RunState) -> List[int]:
    """Return eligible scratch indices (non-protected)."""
    indices = []
    for i, cls in state.message_classifications.items():
        if cls == MessageClassification.SCRATCH.value and i not in state.protected_indices:
            indices.append(i)
    return sorted(indices)


def actions_for(
    node: str,
    turn: int,
    state: RunState,
    scratch_retention: int = 12,
    reposition_after: int = 12,
    reposition_every: int = 4,
    node_exit_cleanup: bool = True,
) -> CacheDecisionResult:
    """Compute cache actions for a given node/turn.

    Pure function with deterministic, testable behaviour.

    Policy (per the master prompt §7):
      - Scratch entries within ``scratch_retention`` count are retained for reuse.
      - Entries beyond the retention window are eligible for dropping.
      - Reposition happens when ``turn > reposition_after`` and every ``reposition_every``
        ticks; reposition is only scheduled when there are eligible scratch entries to move.
      - Node exit cleanup: protect verdicts/evidence then select the remaining eligible
        scratch from this investigation and drop them.
    """
    scratch = _scratch_indices(state)
    if not scratch:
        return CacheDecisionResult(policy_version="1.0")

    protected = set(state.protected_indices)
    # Node-exit cleanup can also touch indices already protected by previous decisions.
    eligible = [idx for idx in scratch if idx not in protected]
    if not eligible:
        return CacheDecisionResult(policy_version="1.0")

    # Drop everything eligible except what stays within the retention window.
    # eligible_threshold = len(eligible) - scratch_retention
    eligible_threshold = len(eligible) - scratch_retention if scratch_retention > 0 else 0
    drop_set = {idx for idx in eligible if eligible_threshold <= idx <= max(eligible)}
    # Hmm — simpler rule: keep the most recent ``scratch_retention`` scratch entries,
    # drop older ones. Indexes from higher turns have more recent content so "most recent"
    # = highest index values when scratches were appended after each turn. We keep those
    # within ``scratch_retention`` from the tail.
    retained = sorted(eligible)[-scratch_retention:] if scratch_retention > 0 else []
    dropped = [idx for idx in eligible if idx not in set(retained)]

    result = CacheDecisionResult(
        drop_message={idx: [] for idx in dropped},
        reposition=[],
        policy_version="1.0",
        historical_prefix_digest=None,
    )

    # Reposition triggers: every ``reposition_every`` ticks once ``turn > reposition_after``.
    if reposition_every > 0 and turn > reposition_after and eligible:
        repositioned = sorted([idx for idx in eligible if idx not in set(dropped)])[:max(len(eligible) // reposition_every * reposition_every, 1)]
        result.reposition = repositioned

    return result


def plan_investigation_exit(
    current_node: str,
    previous_scratch_indices: List[int],
    current_scratch_indices: List[int],
    protected_set: Set[int],
    scratch_retention: int,
) -> CacheDecisionResult:
    """Plan cache cleanup at investigation node boundary.

    Protect verdicts/evidence first, then select remaining eligible scratch.
    """
    remaining = list(current_scratch_indices)

    # Always protect all current scratch on node exit.
    cleanup_indices = [idx for idx in remaining if idx not in protected_set]
    protected_cleanup = [idx for idx in remaining if idx in protected_set]

    if not cleanup_indices:
        return CacheDecisionResult(policy_version="1.0")

    drop_map = {idx: [] for idx in cleanup_indices}
    digest = hashlib.sha256(
        json.dumps({"cleanup": sorted(cleanup_indices)}).encode()
    ).hexdigest()
    return CacheDecisionResult(
        drop_message=drop_map,
        reposition=[],
        policy_version="1.0",
        historical_prefix_digest=digest,
    )


def classify_messages(message_idx: int, state: RunState) -> str:
    """Return classification label for a message index."""
    cls = state.message_classifications.get(message_idx)
    if cls == MessageClassification.SPINE.value:
        return "spine"
    if cls == MessageClassification.REASONING.value:
        return "reasoning"
    return "scratch"
