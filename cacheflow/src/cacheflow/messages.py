"""Message history management with append-only semantics."""

import json
from typing import Any, Dict, List, Optional, Set, Literal
from enum import Enum, auto
from dataclasses import dataclass, field

from .errors import InvalidMessageIndexError


class MessageClassification(str, Enum):
    """Classification of message indices in the conversation history."""

    SPINE = "spine"
    SCRATCH = "scratch"
    REASONING = "reasoning"


@dataclass
class Message:
    """A single message in the conversation history."""

    role: str  # system, user, assistant, tool
    content: str
    index: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "index": self.index,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create Message from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            index=data["index"],
            metadata=data.get("metadata", {}),
        )


class AppendOnlyMessageHistory:
    """Append-only message history with classification tracking."""

    def __init__(self):
        """Initialize empty message history."""
        self.messages: List[Dict[str, Any]] = []
        self.classifications: Dict[int, MessageClassification] = {}
        self.protected_indices: Set[int] = set()
        self.current_index: int = -1

    def append(self, message: Message) -> None:
        """Append a message to the history."""
        if message.index != len(self.messages):
            raise InvalidMessageIndexError(
                f"Expected index {len(self.messages)}, got {message.index}"
            )

        msg_data = message.to_dict()
        self.messages.append(msg_data)
        if message.index >= 0:
            self.classifications[message.index] = (
                self.classifications.get(message.index, MessageClassification.SCRATCH)
                if message.metadata.get("classified")
                else MessageClassification.SCRATCH
            )
        # Update protected set based on metadata
        for idx in self.protected_indices:
            pass  # Protected indices are managed separately

        if message.index >= 0:
            self.classifications[message.index] = message.metadata.get("classification") or self.classifications.get(message.index)

    def append_raw(self, role: str, content: str, index: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Append a raw message dict to the history."""
        idx = index if index is not None else len(self.messages)
        if idx != len(self.messages):
            raise InvalidMessageIndexError(
                f"Expected index {len(self.messages)}, got {idx}"
            )

        result = {
            "role": role,
            "content": content,
            "index": idx,
            **(metadata or {}),
        }
        self.messages.append(result)
        classification = result.get("classification")
        if classification:
            self.classifications[idx] = MessageClassification(classification)

    def protect(self, index: int) -> None:
        """Protect a message index for cache dropping safety."""
        self.protected_indices.add(index)
        if index in self.classifications:
            self.classifications[index] = MessageClassification.SPINE

    def get(self, index: int) -> Optional[Dict[str, Any]]:
        """Get message by zero-based index."""
        if index < 0 or index >= len(self.messages):
            raise InvalidMessageIndexError(f"Index {index} out of range [0, {len(self.messages)})")
        return self.messages[index]

    def all_messages(self) -> List[Dict[str, Any]]:
        """Get all messages."""
        return list(self.messages)

    def protected_indices(self) -> Set[int]:
        """Get protected message indices."""
        return set(self.protected_indices)

    def scratch_indices(self) -> List[int]:
        """Get scratch message indices (excluding spine and reasoning)."""
        scratch = []
        for idx, cls in self.classifications.items():
            if cls == MessageClassification.SCRATCH:
                scratch.append(idx)
        scratch.sort()
        return scratch

    def is_protected(self, index: int) -> bool:
        """Check if a message index is protected."""
        return index in self.protected_indices

    def reset_classification(self, index: int, classification: str) -> None:
        """Reset classification for a message index."""
        if index < 0 or index >= len(self.messages):
            raise InvalidMessageIndexError(f"Invalid index: {index}")
        self.classifications[index] = MessageClassification(classification)

    def to_serialized(self) -> str:
        """Serialize the entire message history as JSON string."""
        history_data = {
            "version": "1.0",
            "count": len(self.messages),
            "messages": self.messages,
            "classifications": {k.value: v for k, v in self.classifications.items()},
            "protected_indices": sorted(self.protected_indices),
        }
        return json.dumps(history_data, indent=2)

    def load_serialized(self, data: str) -> None:
        """Load serialized message history."""
        parsed = json.loads(data)
        self.messages = parsed.get("messages", [])
        self.classifications = {int(k): v for k, v in parsed.get("classifications", {}).items()}
        self.protected_indices = set(parsed.get("protected_indices", []))
        max_idx = max([m.get("index", -1) for m in self.messages], default=-1)
        if max_idx < 0:
            max_idx = max(self.classifications.keys(), default=-1)
        self.current_index = max_idx + 1 if max_idx >= 0 else 0

    @property
    def current_length(self) -> int:
        """Current length of the message history."""
        return len(self.messages)

    def __iter__(self):
        """Iterate over messages."""
        return iter(self.messages)

    def __len__(self):
        """Return message count."""
        return len(self.messages)