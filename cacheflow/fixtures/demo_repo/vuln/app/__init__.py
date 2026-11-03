"""app — application module with a vulnerable pattern."""

import yaml


def load_config(path):
    """Load YAML config from arbitrary path (vulnerable: no allowlist)."""
    with open(path) as f:
        data = yaml.safe_load(f)
    return data


def initialize():
    """Bootstrap from config — calls load_config."""
    cfg = load_config("/etc/app/config.yaml")
    return cfg
