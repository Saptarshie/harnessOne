"""Configuration loading and validation."""

import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class HarnessConfig:
    """Resolved configuration for the harness."""

    # LLM settings
    model: str
    api_base: str
    api_key: str
    max_tokens: int = 4096
    temperature: float = 0.7

    # Harness settings
    max_iterations: int = 5
    sub_agent_count: int = 3
    sub_agent_max_iterations: int = 3
    working_buffer_compact_threshold: int = 4000
    full_compaction_threshold: int = 12000
    stuck_detector: str = "heuristic"

    # Logging settings
    log_level: str = "INFO"
    jsonl_path: str = "logs/traces.jsonl"
    enable_thought_tracking: bool = True


def load_config(config_path: str) -> HarnessConfig:
    """Load and validate configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Resolved HarnessConfig with API key from environment.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If required fields are missing or API key not found.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    llm = raw.get("llm", {})
    harness = raw.get("harness", {})
    logging_cfg = raw.get("logging", {})

    # Resolve API key from environment
    api_key_env = llm.get("api_key_env")
    if not api_key_env:
        raise ValueError("llm.api_key_env is required in config")

    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise ValueError(
            f"API key environment variable '{api_key_env}' is not set"
        )

    # Apply environment overrides
    model = os.environ.get("HARNESS_LLM_MODEL", llm.get("model", "openai/gpt-4o"))
    api_base = llm.get("api_base", "https://api.openai.com/v1")
    max_tokens = llm.get("max_tokens", 4096)
    temperature = llm.get("temperature", 0.7)

    max_iterations = harness.get("max_iterations", 5)
    sub_agent_count = harness.get("sub_agent_count", 3)
    sub_agent_max_iterations = harness.get("sub_agent_max_iterations", 3)
    working_buffer_compact_threshold = harness.get("working_buffer_compact_threshold", 4000)
    full_compaction_threshold = harness.get("full_compaction_threshold", 12000)
    stuck_detector = harness.get("stuck_detector", "heuristic")

    log_level = logging_cfg.get("level", "INFO")
    jsonl_path = logging_cfg.get("jsonl_path", "logs/traces.jsonl")
    enable_thought_tracking = logging_cfg.get("enable_thought_tracking", True)

    return HarnessConfig(
        model=model,
        api_base=api_base,
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
        max_iterations=max_iterations,
        sub_agent_count=sub_agent_count,
        sub_agent_max_iterations=sub_agent_max_iterations,
        working_buffer_compact_threshold=working_buffer_compact_threshold,
        full_compaction_threshold=full_compaction_threshold,
        stuck_detector=stuck_detector,
        log_level=log_level,
        jsonl_path=jsonl_path,
        enable_thought_tracking=enable_thought_tracking,
    )
