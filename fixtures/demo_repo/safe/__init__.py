"""Safety helper: explicit allowlist enforced before any usage."""
from .config import ensure_allowlist


def load(path: str) -> dict:
    return ensure_allowlist(path)
