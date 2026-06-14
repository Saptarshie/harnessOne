"""Configuration loading and validation."""

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Global config location (in the harness repo itself)
GLOBAL_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "global-mcp.yaml"


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

    # Memory settings (v2)
    vault_path: str = "vault"
    embedding_model: str = "Qwen/Qwen3-Embedding-0.6B"
    embedding_device: str = "cpu"
    embedding_quantize: bool = True
    memory_top_k: int = 5
    keyword_weight: float = 0.4
    embedding_weight: float = 0.6
    mcp_server_path: str = "mcp_server/server.py"

    # Session settings (v3)
    session_storage_path: str = "sessions"
    session_auto_save: bool = True
    session_max_history_tokens: int = 100000

    # Skills settings (v3)
    skills_paths: list[str] = field(default_factory=lambda: ["skills/"])
    skills_auto_load: bool = True

    # MCP servers (v3)
    mcp_servers: list[dict] = field(default_factory=list)

    # Tools settings (v3)
    tools_enabled: list[str] = field(default_factory=lambda: ["file_ops", "shell", "git", "search", "web", "skill_ops"])

    # API settings (v3)
    api_enabled: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Self-improvement settings (v3.1)
    improvement_enabled: bool = True
    tracker_storage_path: str = ".harness/prompt_metrics"
    tracker_max_history: int = 1000
    optimizer_enabled: bool = True
    optimizer_min_samples: int = 10
    optimizer_improvement_threshold: float = 0.05
    evolution_enabled: bool = False
    evolution_population_size: int = 20
    evolution_generations: int = 10
    evolution_mutation_rate: float = 0.1
    evolution_crossover_rate: float = 0.7

    # Global memory settings (v3.1)
    global_memory_enabled: bool = True
    global_memory_storage_path: str = ".harness/global_memory"
    global_memory_max_entries: int = 10000

    # Scratchpad settings (v3.1)
    scratchpad_enabled: bool = True
    scratchpad_max_entries: int = 100


def _load_yaml(path: Path) -> dict:
    """Load a YAML file safely."""
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Failed to load {path}: {e}")
        return {}


def _merge_mcp_servers(global_servers: list, local_servers: list) -> list:
    """Merge global and local MCP servers.

    Local servers override global servers with the same name.
    """
    global_servers = global_servers or []
    local_servers = local_servers or []

    # Index global by name
    merged = {}
    for srv in global_servers:
        if isinstance(srv, dict) and srv.get("name"):
            merged[srv["name"]] = srv

    # Local overrides global
    for srv in local_servers:
        if isinstance(srv, dict) and srv.get("name"):
            merged[srv["name"]] = srv

    return list(merged.values())


def load_config(config_path: str, global_config_path: str = None) -> HarnessConfig:
    """Load and validate configuration from a YAML file.

    Automatically loads:
    - .env file from the project root
    - Global MCP config from the harness repo (config/global-mcp.yaml)
    - Local config from the project (.harness/config.yaml)

    Global and local MCP servers are merged (local overrides global).

    Args:
        config_path: Path to the local YAML configuration file.
        global_config_path: Optional path to global config (defaults to harness repo).

    Returns:
        Resolved HarnessConfig with API key from environment.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If required fields are missing or API key not found.
    """
    # Load .env from project root (parent of config/) or same directory
    env_path = Path(config_path).parent.parent / ".env"
    if not env_path.exists():
        env_path = Path(config_path).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # Load global config
    global_path = Path(global_config_path) if global_config_path else GLOBAL_CONFIG_PATH
    global_raw = _load_yaml(global_path)

    # Load local config
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    # Merge MCP servers: global + local (local overrides same name)
    global_mcp = global_raw.get("mcp_servers", [])
    local_mcp = raw.get("mcp_servers", [])
    merged_mcp = _merge_mcp_servers(global_mcp, local_mcp)

    # Merge skills paths: global + local
    global_skills_paths = global_raw.get("skills", {}).get("paths", [])
    local_skills_paths = raw.get("skills", {}).get("paths", [])

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

    memory = raw.get("memory", {})
    vault_path = memory.get("vault_path", "vault")
    embedding_model = memory.get("embedding_model", "Qwen/Qwen3-Embedding-0.6B")
    embedding_device = memory.get("embedding_device", "cpu")
    embedding_quantize = memory.get("embedding_quantize", True)
    memory_top_k = memory.get("top_k", 5)
    keyword_weight = memory.get("keyword_weight", 0.4)
    embedding_weight = memory.get("embedding_weight", 0.6)
    mcp_server_path = memory.get("mcp_server_path", "mcp_server/server.py")

    session = raw.get("session", {})
    skills = raw.get("skills", {})
    tools = raw.get("tools", {})
    api = raw.get("api", {})
    improvement = raw.get("improvement", {})
    global_memory = raw.get("global_memory", {})
    scratchpad = raw.get("scratchpad", {})

    # Parse improvement sub-sections
    tracker = improvement.get("tracker", {})
    optimizer = improvement.get("optimizer", {})
    evolution = improvement.get("evolution", {})

    # Merge all skills paths (global + local)
    all_skills_paths = global_skills_paths + local_skills_paths
    if not all_skills_paths:
        all_skills_paths = ["skills/"]

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
        vault_path=vault_path,
        embedding_model=embedding_model,
        embedding_device=embedding_device,
        embedding_quantize=embedding_quantize,
        memory_top_k=memory_top_k,
        keyword_weight=keyword_weight,
        embedding_weight=embedding_weight,
        mcp_server_path=mcp_server_path,
        session_storage_path=session.get("storage_path", "sessions"),
        session_auto_save=session.get("auto_save", True),
        session_max_history_tokens=session.get("max_history_tokens", 100000),
        skills_paths=all_skills_paths,
        skills_auto_load=skills.get("auto_load", True),
        mcp_servers=merged_mcp,
        tools_enabled=tools.get("enabled", ["file_ops", "shell", "git", "search", "web", "skill_ops"]),
        api_enabled=api.get("enabled", False),
        api_host=api.get("host", "0.0.0.0"),
        api_port=api.get("port", 8000),
        improvement_enabled=improvement.get("enabled", True),
        tracker_storage_path=tracker.get("storage_path", ".harness/prompt_metrics"),
        tracker_max_history=tracker.get("max_history", 1000),
        optimizer_enabled=optimizer.get("enabled", True),
        optimizer_min_samples=optimizer.get("min_samples", 10),
        optimizer_improvement_threshold=optimizer.get("improvement_threshold", 0.05),
        evolution_enabled=evolution.get("enabled", False),
        evolution_population_size=evolution.get("population_size", 20),
        evolution_generations=evolution.get("generations", 10),
        evolution_mutation_rate=evolution.get("mutation_rate", 0.1),
        evolution_crossover_rate=evolution.get("crossover_rate", 0.7),
        global_memory_enabled=global_memory.get("enabled", True),
        global_memory_storage_path=global_memory.get("storage_path", ".harness/global_memory"),
        global_memory_max_entries=global_memory.get("max_entries", 10000),
        scratchpad_enabled=scratchpad.get("enabled", True),
        scratchpad_max_entries=scratchpad.get("max_entries", 100),
    )
