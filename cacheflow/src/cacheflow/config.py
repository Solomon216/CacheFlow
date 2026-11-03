"""Configuration models for CacheFlow runs."""

import os
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, ConfigDict


@dataclass
class RunConfig:
    """Configuration for a CacheFlow run."""

    run_id: str
    workflow: str
    repo: Path
    commit: str
    advisories: Path
    out_dir: Path
    model: str = "llama3.2:1b"
    server_url: str = "http://localhost:8000"
    cache_policy: str = "default"
    max_tool_turns: int = 12
    reposition_interval: int = 4
    protected_indices: Set[int] = field(default_factory=set)
    checkpoint_freq: str = "node"
    tool_permissions: Dict[str, bool] = field(default_factory=lambda: {
        "grep": True,
        "read_file": True,
        "list_dir": True,
        "read_advisory": True,
        "submit_verdict": True,
    })

    def __post_init__(self):
        """Validate and normalize paths."""
        self.repo = Path(self.repo).resolve()
        self.out_dir = Path(self.out_dir).resolve()
        self.out_dir.mkdir(parents=True, exist_ok=True)

        if not self.repo.exists() or not self.repo.is_dir():
            raise ValueError(f"Repository path does not exist: {self.repo}")

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "RunConfig":
        """Create RunConfig from dictionary."""
        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert RunConfig to dictionary."""
        return {
            "run_id": self.run_id,
            "workflow": self.workflow,
            "repo": str(self.repo),
            "commit": self.commit,
            "advisories": str(self.advisories),
            "out_dir": str(self.out_dir),
            "model": self.model,
            "server_url": self.server_url,
            "cache_policy": self.cache_policy,
            "max_tool_turns": self.max_tool_turns,
            "reposition_interval": self.reposition_interval,
            "protected_indices": list(self.protected_indices),
            "checkpoint_freq": self.checkpoint_freq,
            "tool_permissions": self.tool_permissions,
        }


class ServiceConfig(BaseModel):
    """Configuration for external services."""

    model_config = ConfigDict(extra="allow")

    # Model configuration
    model_id: str = Field(..., description="Model identifier")
    max_tokens: int = Field(1024, description="Maximum tokens per response")
    temperature: float = Field(0.0, description="Temperature for generation")
    top_p: float = Field(1.0, description="Top-p sampling parameter")

    # AKV server configuration
    akv_server_url: str = Field(..., description="AKV server URL")
    akv_api_key: Optional[str] = Field(None, description="AKV API key")
    akv_model: str = Field("default", description="AKV model name")

    # Serving configuration
    max_batch_size: int = Field(8, description="Maximum batch size")
    max_concurrent_requests: int = Field(100, description="Maximum concurrent requests")

    # Retry configuration
    max_retries: int = Field(3, description="Maximum retry attempts")
    retry_delay: float = Field(1.0, description="Delay between retries")

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Temperature must be between 0.0 and 1.0")
        return v

    @field_validator("top_p")
    @classmethod
    def validate_top_p(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Top-p must be between 0.0 and 1.0")
        return v

    @field_validator("max_batch_size")
    @classmethod
    def validate_batch_size(cls, v):
        if v <= 0:
            raise ValueError("Batch size must be positive")
        return v