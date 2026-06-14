# Cognitive LLM Harness — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a plugin-based LLM reasoning harness with dynamic thinking, stuck detection, parallel sub-agents, lean compaction, and structured logging.

**Architecture:** Plugin architecture with LangGraph orchestration. Each reasoning step (think, detect stuck, spawn sub-agents, compact) is a standalone plugin node registered via decorator. A central Orchestrator builds the LangGraph graph and executes it. Single `harness.invoke()` entry point hides all internal machinery.

**Tech Stack:** Python 3.11+, LiteLLM, LangGraph, PyYAML, tiktoken, pytest, pytest-asyncio

**Spec:** `docs/superpowers/specs/2026-06-14-cognitive-llm-harness-design.md`

---

## File Map

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Project metadata, dependencies |
| `config/default.yaml` | Default configuration |
| `src/harness/__init__.py` | Package root, `invoke()` entry point |
| `src/harness/config.py` | YAML config loading, validation, env var resolution |
| `src/harness/state.py` | `HarnessState` TypedDict |
| `src/harness/llm/__init__.py` | LLM package init |
| `src/harness/llm/client.py` | LiteLLM wrapper: async calls, token counting, retry |
| `src/harness/plugins/__init__.py` | Plugin registry, `@register_node` decorator |
| `src/harness/plugins/base.py` | `BaseNode` ABC |
| `src/harness/plugins/thinker.py` | Main LLM reasoning node |
| `src/harness/plugins/stuck_detector.py` | Metacognitive stuck detection |
| `src/harness/plugins/sub_agent_spawner.py` | Parallel sub-agent forking |
| `src/harness/plugins/compactor.py` | Lean-style compaction into checkpoints |
| `src/harness/plugins/context_manager.py` | Context window management, two-tier compaction triggers |
| `src/harness/logging/__init__.py` | Logging package init |
| `src/harness/logging/trace_logger.py` | Structured JSONL execution traces |
| `src/harness/orchestrator.py` | Plugin discovery, LangGraph graph builder, execution |
| `tests/unit/test_config.py` | Config module tests |
| `tests/unit/test_llm_client.py` | LLM client tests |
| `tests/unit/test_thinker.py` | Thinker plugin tests |
| `tests/unit/test_stuck_detector.py` | Stuck detector tests |
| `tests/unit/test_sub_agent_spawner.py` | Sub-agent spawner tests |
| `tests/unit/test_compactor.py` | Compactor tests |
| `tests/unit/test_context_manager.py` | Context manager tests |
| `tests/unit/test_trace_logger.py` | Trace logger tests |
| `tests/integration/test_full_cycle.py` | Full harness integration tests |

---

## Task 0: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `config/default.yaml`
- Create: `src/harness/__init__.py`
- Create: `src/harness/llm/__init__.py`
- Create: `src/harness/plugins/__init__.py`
- Create: `src/harness/logging/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/integration/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "cognitive-harness"
version = "0.1.0"
description = "Plugin-based LLM reasoning harness with dynamic thinking"
requires-python = ">=3.11"
dependencies = [
    "litellm>=1.40.0",
    "langgraph>=0.2.0",
    "pyyaml>=6.0",
    "tiktoken>=0.7.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-mock>=3.12",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "integration: marks tests as integration tests (require real LLM)",
]
```

- [ ] **Step 2: Create directory structure**

Run:
```powershell
New-Item -ItemType Directory -Path "src/harness/llm" -Force
New-Item -ItemType Directory -Path "src/harness/plugins" -Force
New-Item -ItemType Directory -Path "src/harness/logging" -Force
New-Item -ItemType Directory -Path "config" -Force
New-Item -ItemType Directory -Path "tests/unit" -Force
New-Item -ItemType Directory -Path "tests/integration" -Force
```

- [ ] **Step 3: Create all __init__.py files**

`src/harness/__init__.py`:
```python
"""Cognitive LLM Harness — plugin-based reasoning engine."""
```

`src/harness/llm/__init__.py`:
```python
"""LLM client module."""
```

`src/harness/plugins/__init__.py`:
```python
"""Plugin registry and built-in plugins."""
```

`src/harness/logging/__init__.py`:
```python
"""Structured logging and telemetry."""
```

`tests/__init__.py`:
```python
```

`tests/unit/__init__.py`:
```python
```

`tests/integration/__init__.py`:
```python
```

- [ ] **Step 4: Create default config**

`config/default.yaml`:
```yaml
llm:
  model: "openai/gpt-4o"
  api_base: "https://api.openai.com/v1"
  api_key_env: "OPENAI_API_KEY"
  max_tokens: 4096
  temperature: 0.7

harness:
  max_iterations: 5
  sub_agent_count: 3
  sub_agent_max_iterations: 3
  working_buffer_compact_threshold: 4000
  full_compaction_threshold: 12000
  stuck_detector: "heuristic"

logging:
  level: "INFO"
  jsonl_path: "logs/traces.jsonl"
  enable_thought_tracking: true
```

- [ ] **Step 5: Install dependencies and verify**

Run:
```powershell
pip install -e ".[dev]"
```

Expected: Successful installation with no errors.

- [ ] **Step 6: Verify pytest works**

Run:
```powershell
pytest --co
```

Expected: "no tests ran" (collects nothing, but no errors).

- [ ] **Step 7: Commit**

```powershell
git init
git add .
git commit -m "feat: project setup with pyproject.toml, config, and directory structure"
```

---

## Task 1: Config Module

**Files:**
- Create: `src/harness/config.py`
- Create: `tests/unit/test_config.py`

- [ ] **Step 1: Write failing tests for config**

`tests/unit/test_config.py`:
```python
import os
import pytest
import tempfile
import yaml
from harness.config import HarnessConfig, load_config


class TestHarnessConfig:
    def test_default_values(self):
        config = HarnessConfig(
            model="openai/gpt-4o",
            api_base="https://api.openai.com/v1",
            api_key="test-key",
        )
        assert config.model == "openai/gpt-4o"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.max_iterations == 5
        assert config.sub_agent_count == 3

    def test_custom_values(self):
        config = HarnessConfig(
            model="openai/gpt-4o-mini",
            api_base="http://localhost:8000",
            api_key="test-key",
            max_tokens=2048,
            temperature=0.3,
            max_iterations=10,
        )
        assert config.max_tokens == 2048
        assert config.temperature == 0.3
        assert config.max_iterations == 10


class TestLoadConfig:
    def test_load_from_yaml(self, tmp_path):
        config_data = {
            "llm": {
                "model": "openai/gpt-4o",
                "api_base": "https://api.openai.com/v1",
                "api_key_env": "TEST_API_KEY",
                "max_tokens": 4096,
                "temperature": 0.7,
            },
            "harness": {
                "max_iterations": 5,
                "sub_agent_count": 3,
                "sub_agent_max_iterations": 3,
                "working_buffer_compact_threshold": 4000,
                "full_compaction_threshold": 12000,
                "stuck_detector": "heuristic",
            },
            "logging": {
                "level": "INFO",
                "jsonl_path": "logs/traces.jsonl",
                "enable_thought_tracking": True,
            },
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        os.environ["TEST_API_KEY"] = "sk-test-123"
        try:
            config = load_config(str(config_file))
            assert config.model == "openai/gpt-4o"
            assert config.api_key == "sk-test-123"
            assert config.max_iterations == 5
        finally:
            del os.environ["TEST_API_KEY"]

    def test_missing_api_key_raises(self, tmp_path):
        config_data = {
            "llm": {
                "model": "openai/gpt-4o",
                "api_base": "https://api.openai.com/v1",
                "api_key_env": "NONEXISTENT_KEY",
            },
            "harness": {"max_iterations": 5},
            "logging": {"level": "INFO"},
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ValueError, match="API key"):
            load_config(str(config_file))

    def test_missing_config_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.yaml")

    def test_env_override(self, tmp_path):
        config_data = {
            "llm": {
                "model": "openai/gpt-4o",
                "api_base": "https://api.openai.com/v1",
                "api_key_env": "TEST_API_KEY",
            },
            "harness": {"max_iterations": 5},
            "logging": {"level": "INFO"},
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        os.environ["TEST_API_KEY"] = "sk-test-123"
        os.environ["HARNESS_LLM_MODEL"] = "openai/gpt-4o-mini"
        try:
            config = load_config(str(config_file))
            assert config.model == "openai/gpt-4o-mini"
        finally:
            del os.environ["TEST_API_KEY"]
            del os.environ["HARNESS_LLM_MODEL"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```powershell
pytest tests/unit/test_config.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'harness.config'`

- [ ] **Step 3: Implement config module**

`src/harness/config.py`:
```python
"""Configuration loading and validation."""

import os
from dataclasses import dataclass, field
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```powershell
pytest tests/unit/test_config.py -v
```
Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/harness/config.py tests/unit/test_config.py
git commit -m "feat: config module with YAML loading and env var resolution"
```

---

## Task 2: LLM Client

**Files:**
- Create: `src/harness/llm/client.py`
- Create: `tests/unit/test_llm_client.py`

- [ ] **Step 1: Write failing tests for LLM client**

`tests/unit/test_llm_client.py`:
```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from harness.llm.client import LLMClient, LLMResponse
from harness.config import HarnessConfig


@pytest.fixture
def config():
    return HarnessConfig(
        model="openai/gpt-4o",
        api_base="https://api.openai.com/v1",
        api_key="sk-test-123",
        max_tokens=4096,
        temperature=0.7,
    )


@pytest.fixture
def client(config):
    return LLMClient(config)


class TestLLMResponse:
    def test_response_attributes(self):
        resp = LLMResponse(
            content="Hello",
            input_tokens=10,
            output_tokens=5,
            model="openai/gpt-4o",
            finish_reason="stop",
        )
        assert resp.content == "Hello"
        assert resp.input_tokens == 10
        assert resp.output_tokens == 5


class TestCountTokens:
    def test_count_tokens_returns_int(self, client):
        messages = [{"role": "user", "content": "Hello world"}]
        count = client.count_tokens(messages)
        assert isinstance(count, int)
        assert count > 0

    def test_count_tokens_multiple_messages(self, client):
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"},
        ]
        count = client.count_tokens(messages)
        assert count > 5


class TestLLMCall:
    @pytest.mark.asyncio
    async def test_call_returns_response(self, client):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "4"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.model = "openai/gpt-4o"

        with patch("harness.llm.client.acompletion", new_callable=AsyncMock, return_value=mock_response):
            response = await client.call([{"role": "user", "content": "What is 2+2?"}])

        assert isinstance(response, LLMResponse)
        assert response.content == "4"
        assert response.input_tokens == 10
        assert response.output_tokens == 5

    @pytest.mark.asyncio
    async def test_call_retries_on_failure(self, client):
        mock_success = MagicMock()
        mock_success.choices = [MagicMock()]
        mock_success.choices[0].message.content = "ok"
        mock_success.choices[0].finish_reason = "stop"
        mock_success.usage.prompt_tokens = 5
        mock_success.usage.completion_tokens = 3
        mock_success.model = "openai/gpt-4o"

        with patch(
            "harness.llm.client.acompletion",
            new_callable=AsyncMock,
            side_effect=[Exception("timeout"), mock_success],
        ):
            response = await client.call([{"role": "user", "content": "test"}])
        assert response.content == "ok"

    @pytest.mark.asyncio
    async def test_call_raises_after_max_retries(self, client):
        with patch(
            "harness.llm.client.acompletion",
            new_callable=AsyncMock,
            side_effect=Exception("persistent failure"),
        ):
            with pytest.raises(Exception, match="persistent failure"):
                await client.call([{"role": "user", "content": "test"}])
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```powershell
pytest tests/unit/test_llm_client.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'harness.llm.client'`

- [ ] **Step 3: Implement LLM client**

`src/harness/llm/client.py`:
```python
"""LiteLLM wrapper with retry, token counting, and logging."""

import asyncio
import logging
from dataclasses import dataclass

import tiktoken
from litellm import acompletion

from harness.config import HarnessConfig

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Structured response from an LLM call."""

    content: str
    input_tokens: int
    output_tokens: int
    model: str
    finish_reason: str


class LLMClient:
    """Async LLM client wrapping LiteLLM with retry and token counting."""

    def __init__(self, config: HarnessConfig):
        self.config = config
        self._encoder = self._get_encoder(config.model)

    def _get_encoder(self, model: str) -> tiktoken.Encoding:
        """Get tiktoken encoder for the model."""
        try:
            return tiktoken.encoding_for_model(model.split("/")[-1])
        except KeyError:
            return tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, messages: list[dict]) -> int:
        """Count tokens in a list of messages.

        Args:
            messages: List of message dicts with 'role' and 'content'.

        Returns:
            Total token count.
        """
        total = 0
        for msg in messages:
            # Each message has overhead for role and formatting
            total += 4  # role + separators
            content = msg.get("content", "")
            total += len(self._encoder.encode(content))
        total += 2  # priming tokens
        return total

    async def call(
        self,
        messages: list[dict],
        max_retries: int = 3,
        base_delay: float = 1.0,
        **kwargs,
    ) -> LLMResponse:
        """Call the LLM with retry logic.

        Args:
            messages: List of message dicts.
            max_retries: Maximum retry attempts.
            base_delay: Base delay for exponential backoff.
            **kwargs: Additional arguments passed to acompletion.

        Returns:
            LLMResponse with content and usage info.

        Raises:
            Exception: If all retries fail.
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                response = await acompletion(
                    model=self.config.model,
                    api_base=self.config.api_base,
                    api_key=self.config.api_key,
                    messages=messages,
                    max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                    temperature=kwargs.get("temperature", self.config.temperature),
                )

                choice = response.choices[0]
                return LLMResponse(
                    content=choice.message.content or "",
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    model=response.model,
                    finish_reason=choice.finish_reason or "unknown",
                )
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)

        raise last_exception
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```powershell
pytest tests/unit/test_llm_client.py -v
```
Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/harness/llm/client.py tests/unit/test_llm_client.py
git commit -m "feat: LLM client with LiteLLM wrapper, retry, and token counting"
```

---

## Task 3: State Definition

**Files:**
- Create: `src/harness/state.py`

- [ ] **Step 1: Create state module**

`src/harness/state.py`:
```python
"""Shared state definition for the harness."""

from typing import TypedDict


class HarnessState(TypedDict):
    """State passed between harness plugins during execution."""

    # Core conversation
    checkpoints: list[str]
    working_buffer: list[dict]

    # Reasoning control
    is_stuck: bool
    sub_agent_results: list[dict]
    current_response: str

    # Execution metadata
    trace_id: str
    iteration: int
    max_iterations: int
    metadata: dict


def create_initial_state(
    trace_id: str,
    max_iterations: int,
    initial_prompt: str,
) -> HarnessState:
    """Create a fresh HarnessState for a new invocation.

    Args:
        trace_id: Unique identifier for this execution.
        max_iterations: Maximum thinking iterations allowed.
        initial_prompt: The user's input prompt.

    Returns:
        Initialized HarnessState.
    """
    return HarnessState(
        checkpoints=[],
        working_buffer=[{"role": "user", "content": initial_prompt}],
        is_stuck=False,
        sub_agent_results=[],
        current_response="",
        trace_id=trace_id,
        iteration=0,
        max_iterations=max_iterations,
        metadata={},
    )
```

- [ ] **Step 2: Verify import works**

Run:
```powershell
python -c "from harness.state import HarnessState, create_initial_state; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```powershell
git add src/harness/state.py
git commit -m "feat: shared HarnessState TypedDict and factory"
```

---

## Task 4: Plugin System (Base + Registry)

**Files:**
- Create: `src/harness/plugins/base.py`
- Modify: `src/harness/plugins/__init__.py`
- Create: `tests/unit/test_plugin_registry.py`

- [ ] **Step 1: Write failing tests for plugin registry**

`tests/unit/test_plugin_registry.py`:
```python
import pytest
from harness.plugins import get_registered_nodes, clear_registry
from harness.plugins.base import BaseNode
from harness.state import HarnessState
from harness.llm.client import LLMClient


class TestPluginRegistry:
    def setup_method(self):
        clear_registry()

    def teardown_method(self):
        clear_registry()

    def test_register_and_retrieve(self):
        from harness.plugins import register_node

        @register_node("test_node")
        class TestNode(BaseNode):
            name = "test_node"

            async def process(self, state: HarnessState, llm: LLMClient) -> HarnessState:
                return state

        nodes = get_registered_nodes()
        assert "test_node" in nodes
        assert nodes["test_node"] is TestNode

    def test_multiple_registrations(self):
        from harness.plugins import register_node

        @register_node("node_a")
        class NodeA(BaseNode):
            name = "node_a"

            async def process(self, state, llm):
                return state

        @register_node("node_b")
        class NodeB(BaseNode):
            name = "node_b"

            async def process(self, state, llm):
                return state

        nodes = get_registered_nodes()
        assert len(nodes) == 2
        assert "node_a" in nodes
        assert "node_b" in nodes

    def test_clear_registry(self):
        from harness.plugins import register_node

        @register_node("temp_node")
        class TempNode(BaseNode):
            name = "temp_node"

            async def process(self, state, llm):
                return state

        assert len(get_registered_nodes()) == 1
        clear_registry()
        assert len(get_registered_nodes()) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```powershell
pytest tests/unit/test_plugin_registry.py -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement base node and registry**

`src/harness/plugins/base.py`:
```python
"""Base class for all harness plugins."""

from abc import ABC, abstractmethod

from harness.state import HarnessState
from harness.llm.client import LLMClient


class BaseNode(ABC):
    """Abstract base class for harness plugin nodes.

    Each plugin implements a single step of the reasoning loop.
    Plugins receive state and an LLM client, and return modified state.
    """

    name: str

    @abstractmethod
    async def process(self, state: HarnessState, llm: LLMClient) -> HarnessState:
        """Process state and return modified state.

        Args:
            state: Current harness state.
            llm: LLM client for making model calls.

        Returns:
            Modified harness state.
        """
        ...
```

`src/harness/plugins/__init__.py`:
```python
"""Plugin registry and built-in plugins."""

from harness.plugins.base import BaseNode

# Global plugin registry
_registry: dict[str, type[BaseNode]] = {}


def register_node(name: str):
    """Decorator to register a plugin node.

    Usage:
        @register_node("my_node")
        class MyNode(BaseNode):
            name = "my_node"
            async def process(self, state, llm):
                ...
    """
    def decorator(cls: type[BaseNode]):
        _registry[name] = cls
        return cls
    return decorator


def get_registered_nodes() -> dict[str, type[BaseNode]]:
    """Return a copy of the current plugin registry."""
    return dict(_registry)


def clear_registry():
    """Clear all registered plugins. Used in testing."""
    _registry.clear()
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```powershell
pytest tests/unit/test_plugin_registry.py -v
```
Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/harness/plugins/base.py src/harness/plugins/__init__.py tests/unit/test_plugin_registry.py
git commit -m "feat: plugin system with BaseNode ABC and registry decorator"
```

---

## Task 5: Trace Logger

**Files:**
- Create: `src/harness/logging/trace_logger.py`
- Create: `tests/unit/test_trace_logger.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_trace_logger.py`:
```python
import json
import pytest
from harness.logging.trace_logger import TraceLogger


class TestTraceLogger:
    def test_log_entry_written(self, tmp_path):
        log_file = tmp_path / "traces.jsonl"
        logger = TraceLogger(str(log_file))

        logger.log(
            trace_id="test-123",
            node="thinker",
            iteration=0,
            input_tokens=100,
            output_tokens=50,
            success=True,
        )

        logger.flush()

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 1

        entry = json.loads(lines[0])
        assert entry["trace_id"] == "test-123"
        assert entry["node"] == "thinker"
        assert entry["input_tokens"] == 100
        assert entry["output_tokens"] == 50
        assert entry["success"] is True
        assert "timestamp" in entry
        assert "duration_ms" in entry

    def test_multiple_entries(self, tmp_path):
        log_file = tmp_path / "traces.jsonl"
        logger = TraceLogger(str(log_file))

        for i in range(3):
            logger.log(
                trace_id="test-123",
                node=f"node_{i}",
                iteration=i,
                input_tokens=10 * i,
                output_tokens=5 * i,
                success=True,
            )

        logger.flush()

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 3

    def test_metadata_preserved(self, tmp_path):
        log_file = tmp_path / "traces.jsonl"
        logger = TraceLogger(str(log_file))

        logger.log(
            trace_id="test-123",
            node="compactor",
            iteration=1,
            input_tokens=100,
            output_tokens=50,
            success=True,
            checkpoint_created="B'",
            sub_agents_used=["path_1", "path_2"],
        )

        logger.flush()

        entry = json.loads(log_file.read_text().strip())
        assert entry["checkpoint_created"] == "B'"
        assert entry["sub_agents_used"] == ["path_1", "path_2"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```powershell
pytest tests/unit/test_trace_logger.py -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement trace logger**

`src/harness/logging/trace_logger.py`:
```python
"""Structured JSONL execution trace logger."""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


class TraceLogger:
    """Append-only JSONL logger for execution traces.

    Each entry is a JSON object with standard fields plus arbitrary metadata.
    """

    def __init__(self, log_path: str):
        self._path = Path(log_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._buffer: list[dict] = []
        self._start_times: dict[str, float] = {}

    def log(
        self,
        trace_id: str,
        node: str,
        iteration: int,
        input_tokens: int,
        output_tokens: int,
        success: bool,
        **metadata,
    ) -> None:
        """Log a trace entry.

        Args:
            trace_id: Execution trace ID.
            node: Plugin name that generated this entry.
            iteration: Current harness iteration.
            input_tokens: Tokens in the input.
            output_tokens: Tokens in the output.
            success: Whether the operation succeeded.
            **metadata: Additional key-value pairs to include.
        """
        now = time.time()
        key = f"{trace_id}:{node}:{iteration}"

        # Track duration if we have a start time
        duration_ms = None
        if key in self._start_times:
            duration_ms = int((now - self._start_times[key]) * 1000)
            del self._start_times[key]

        entry = {
            "trace_id": trace_id,
            "node": node,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "iteration": iteration,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "success": success,
            "duration_ms": duration_ms,
            **metadata,
        }

        self._buffer.append(entry)

    def start_timer(self, trace_id: str, node: str, iteration: int) -> None:
        """Start a timer for measuring node execution duration."""
        key = f"{trace_id}:{node}:{iteration}"
        self._start_times[key] = time.time()

    def flush(self) -> None:
        """Write all buffered entries to disk."""
        with open(self._path, "a", encoding="utf-8") as f:
            for entry in self._buffer:
                f.write(json.dumps(entry) + "\n")
        self._buffer.clear()
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```powershell
pytest tests/unit/test_trace_logger.py -v
```
Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/harness/logging/trace_logger.py tests/unit/test_trace_logger.py
git commit -m "feat: structured JSONL trace logger"
```

---

## Task 6: Thinker Plugin

**Files:**
- Create: `src/harness/plugins/thinker.py`
- Create: `tests/unit/test_thinker.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_thinker.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.plugins.thinker import ThinkerNode
from harness.llm.client import LLMResponse
from harness.state import HarnessState


@pytest.fixture
def state():
    return HarnessState(
        checkpoints=["Checkpoint A: The user wants to fix a bug."],
        working_buffer=[
            {"role": "user", "content": "Fix the bug in main.py"},
            {"role": "assistant", "content": "Let me analyze the code..."},
        ],
        is_stuck=False,
        sub_agent_results=[],
        current_response="",
        trace_id="test-123",
        iteration=0,
        max_iterations=5,
        metadata={},
    )


class TestThinkerNode:
    @pytest.mark.asyncio
    async def test_appends_response_to_working_buffer(self, state):
        mock_llm = MagicMock()
        mock_llm.call = AsyncMock(
            return_value=LLMResponse(
                content="I found the bug: line 42 has an off-by-one error.",
                input_tokens=100,
                output_tokens=50,
                model="openai/gpt-4o",
                finish_reason="stop",
            )
        )
        mock_llm.count_tokens = MagicMock(return_value=150)

        node = ThinkerNode()
        result = await node.process(state, mock_llm)

        assert len(result["working_buffer"]) == 3
        assert result["working_buffer"][-1]["role"] == "assistant"
        assert "off-by-one" in result["working_buffer"][-1]["content"]
        assert result["current_response"] == "I found the bug: line 42 has an off-by-one error."

    @pytest.mark.asyncio
    async def test_assembles_context_from_checkpoints_and_buffer(self, state):
        mock_llm = MagicMock()
        captured_messages = []

        async def capture_call(messages, **kwargs):
            captured_messages.extend(messages)
            return LLMResponse(
                content="response",
                input_tokens=100,
                output_tokens=50,
                model="openai/gpt-4o",
                finish_reason="stop",
            )

        mock_llm.call = capture_call
        mock_llm.count_tokens = MagicMock(return_value=150)

        node = ThinkerNode()
        await node.process(state, mock_llm)

        # Should have system message with checkpoints + buffer messages
        assert len(captured_messages) >= 3
        system_msg = captured_messages[0]
        assert system_msg["role"] == "system"
        assert "Checkpoint A" in system_msg["content"]

    @pytest.mark.asyncio
    async def test_extracts_thought_blocks(self, state):
        mock_llm = MagicMock()
        mock_llm.call = AsyncMock(
            return_value=LLMResponse(
                content="<thought>I need to check the loop bounds</thought>The fix is to change < to <=.",
                input_tokens=100,
                output_tokens=50,
                model="openai/gpt-4o",
                finish_reason="stop",
            )
        )
        mock_llm.count_tokens = MagicMock(return_value=150)

        node = ThinkerNode()
        result = await node.process(state, mock_llm)

        assert result["metadata"]["last_thought"] == "I need to check the loop bounds"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```powershell
pytest tests/unit/test_thinker.py -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement thinker plugin**

`src/harness/plugins/thinker.py`:
```python
"""Main LLM reasoning plugin."""

import re

from harness.plugins import register_node
from harness.plugins.base import BaseNode
from harness.state import HarnessState
from harness.llm.client import LLMClient


@register_node("thinker")
class ThinkerNode(BaseNode):
    """Main reasoning node. Calls the LLM with assembled context."""

    name = "thinker"

    async def process(self, state: HarnessState, llm: LLMClient) -> HarnessState:
        """Run the main LLM reasoning step.

        Assembles context from checkpoints + working buffer, calls the LLM,
        and appends the response to the working buffer.
        """
        messages = self._assemble_context(state)
        response = await llm.call(messages)

        # Extract thought blocks for tracking
        thought = self._extract_thought(response.content)
        if thought:
            state.setdefault("metadata", {})["last_thought"] = thought

        # Append response to working buffer
        state["working_buffer"].append({
            "role": "assistant",
            "content": response.content,
        })
        state["current_response"] = response.content

        return state

    def _assemble_context(self, state: HarnessState) -> list[dict]:
        """Build the message list for the LLM call.

        Combines checkpoints into a system message, then includes the working buffer.
        """
        messages = []

        # System message with all checkpoints
        if state["checkpoints"]:
            checkpoint_text = "\n\n".join(
                f"[Checkpoint {chr(65 + i)}]: {cp}"
                for i, cp in enumerate(state["checkpoints"])
            )
            messages.append({
                "role": "system",
                "content": (
                    "You are a reasoning engine. Here are your verified reasoning checkpoints:\n\n"
                    f"{checkpoint_text}\n\n"
                    "Continue reasoning from where the last checkpoint left off."
                ),
            })
        else:
            messages.append({
                "role": "system",
                "content": "You are a reasoning engine. Think step by step.",
            })

        # Add working buffer messages
        messages.extend(state["working_buffer"])

        return messages

    def _extract_thought(self, content: str) -> str | None:
        """Extract content from <thought> tags."""
        match = re.search(r"<thought>(.*?)</thought>", content, re.DOTALL)
        return match.group(1).strip() if match else None
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```powershell
pytest tests/unit/test_thinker.py -v
```
Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/harness/plugins/thinker.py tests/unit/test_thinker.py
git commit -m "feat: ThinkerPlugin with context assembly and thought extraction"
```

---

## Task 7: Stuck Detector Plugin

**Files:**
- Create: `src/harness/plugins/stuck_detector.py`
- Create: `tests/unit/test_stuck_detector.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_stuck_detector.py`:
```python
import pytest
from unittest.mock import MagicMock
from harness.plugins.stuck_detector import StuckDetectorNode
from harness.state import HarnessState


def make_state(assistant_messages: list[str]) -> HarnessState:
    buffer = [{"role": "user", "content": "Fix the bug"}]
    for msg in assistant_messages:
        buffer.append({"role": "assistant", "content": msg})
    return HarnessState(
        checkpoints=[],
        working_buffer=buffer,
        is_stuck=False,
        sub_agent_results=[],
        current_response="",
        trace_id="test-123",
        iteration=0,
        max_iterations=5,
        metadata={},
    )


class TestStuckDetectorNode:
    @pytest.mark.asyncio
    async def test_not_stuck_on_first_response(self):
        state = make_state(["Let me look at the code."])
        mock_llm = MagicMock()

        node = StuckDetectorNode()
        result = await node.process(state, mock_llm)

        assert result["is_stuck"] is False

    @pytest.mark.asyncio
    async def test_stuck_on_repeated_phrases(self):
        state = make_state([
            "I think the issue is in the loop.",
            "Let me try again. I think the issue is in the loop.",
            "Hmm, I think the issue is in the loop.",
        ])
        mock_llm = MagicMock()

        node = StuckDetectorNode()
        result = await node.process(state, mock_llm)

        assert result["is_stuck"] is True

    @pytest.mark.asyncio
    async def test_stuck_on_hedging_language(self):
        state = make_state([
            "I'm not sure about this. Let me try something else.",
            "Maybe the issue is somewhere else. I'm not sure.",
            "Let me try again. I'm not sure what's happening.",
        ])
        mock_llm = MagicMock()

        node = StuckDetectorNode()
        result = await node.process(state, mock_llm)

        assert result["is_stuck"] is True

    @pytest.mark.asyncio
    async def test_not_stuck_on_progress(self):
        state = make_state([
            "I found the issue in line 10.",
            "The fix is to add a null check.",
            "I've applied the fix and the tests pass.",
        ])
        mock_llm = MagicMock()

        node = StuckDetectorNode()
        result = await node.process(state, mock_llm)

        assert result["is_stuck"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```powershell
pytest tests/unit/test_stuck_detector.py -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement stuck detector**

`src/harness/plugins/stuck_detector.py`:
```python
"""Metacognitive stuck detection plugin."""

import re
from collections import Counter

from harness.plugins import register_node
from harness.plugins.base import BaseNode
from harness.state import HarnessState
from harness.llm.client import LLMClient


# Phrases that indicate hedging or uncertainty
HEDGING_PATTERNS = [
    r"i'?m not sure",
    r"maybe",
    r"let me try (again|something else|another approach)",
    r"i don'?t (know|understand)",
    r"this isn'?t working",
    r"i'?m stuck",
    r"going in circles",
]


@register_node("stuck_detector")
class StuckDetectorNode(BaseNode):
    """Detects whether the model is stuck in a reasoning loop."""

    name = "stuck_detector"

    async def process(self, state: HarnessState, llm: LLMClient) -> HarnessState:
        """Analyze recent messages for signs of being stuck.

        Detection heuristics:
        1. Repeated phrases across assistant messages
        2. High density of hedging/uncertainty language
        3. Contradiction markers
        """
        assistant_messages = [
            msg["content"]
            for msg in state["working_buffer"]
            if msg.get("role") == "assistant"
        ]

        if len(assistant_messages) < 2:
            state["is_stuck"] = False
            return state

        is_stuck = False

        # Check for repeated phrases
        if self._has_repeated_phrases(assistant_messages):
            is_stuck = True

        # Check for hedging language
        if self._has_excessive_hedging(assistant_messages):
            is_stuck = True

        state["is_stuck"] = is_stuck
        return state

    def _has_repeated_phrases(self, messages: list[str]) -> bool:
        """Check if the same phrases appear across multiple messages."""
        # Extract 4-word phrases from each message
        all_phrases: list[str] = []
        for msg in messages[-5:]:  # Last 5 messages
            words = msg.lower().split()
            for i in range(len(words) - 3):
                phrase = " ".join(words[i : i + 4])
                all_phrases.append(phrase)

        if not all_phrases:
            return False

        counter = Counter(all_phrases)
        # If any 4-word phrase appears 3+ times, we're likely looping
        most_common_count = counter.most_common(1)[0][1] if counter else 0
        return most_common_count >= 3

    def _has_excessive_hedging(self, messages: list[str]) -> bool:
        """Check if recent messages have high density of hedging language."""
        recent = " ".join(messages[-3:]).lower()
        hedging_count = sum(
            1 for pattern in HEDGING_PATTERNS if re.search(pattern, recent)
        )
        # 3+ hedging patterns in recent messages = likely stuck
        return hedging_count >= 3
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```powershell
pytest tests/unit/test_stuck_detector.py -v
```
Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/harness/plugins/stuck_detector.py tests/unit/test_stuck_detector.py
git commit -m "feat: StuckDetector with phrase repetition and hedging heuristics"
```

---

## Task 8: Sub-Agent Spawner Plugin

**Files:**
- Create: `src/harness/plugins/sub_agent_spawner.py`
- Create: `tests/unit/test_sub_agent_spawner.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_sub_agent_spawner.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.plugins.sub_agent_spawner import SubAgentSpawnerNode
from harness.llm.client import LLMResponse
from harness.state import HarnessState


@pytest.fixture
def stuck_state():
    return HarnessState(
        checkpoints=["Checkpoint A: debugging memory leak"],
        working_buffer=[
            {"role": "user", "content": "Fix the memory leak"},
            {"role": "assistant", "content": "I tried reducing batch size but it didn't work."},
        ],
        is_stuck=True,
        sub_agent_results=[],
        current_response="I tried reducing batch size but it didn't work.",
        trace_id="test-123",
        iteration=1,
        max_iterations=5,
        metadata={},
    )


def make_mock_llm(response_text: str):
    mock_llm = MagicMock()
    mock_llm.call = AsyncMock(
        return_value=LLMResponse(
            content=response_text,
            input_tokens=100,
            output_tokens=50,
            model="openai/gpt-4o",
            finish_reason="stop",
        )
    )
    mock_llm.count_tokens = MagicMock(return_value=150)
    return mock_llm


class TestSubAgentSpawnerNode:
    @pytest.mark.asyncio
    async def test_spawns_sub_agents(self, stuck_state):
        mock_llm = make_mock_llm("Try using gradient checkpointing.")

        node = SubAgentSpawnerNode(sub_agent_count=3)
        result = await node.process(stuck_state, mock_llm)

        assert len(result["sub_agent_results"]) == 3
        assert result["is_stuck"] is True  # Still stuck until compactor runs

    @pytest.mark.asyncio
    async def test_each_sub_agent_gets_checkpoint_context(self, stuck_state):
        captured_messages = []

        async def capture_call(messages, **kwargs):
            captured_messages.append(messages)
            return LLMResponse(
                content="suggestion",
                input_tokens=100,
                output_tokens=50,
                model="openai/gpt-4o",
                finish_reason="stop",
            )

        mock_llm = MagicMock()
        mock_llm.call = capture_call
        mock_llm.count_tokens = MagicMock(return_value=150)

        node = SubAgentSpawnerNode(sub_agent_count=2)
        await node.process(stuck_state, mock_llm)

        # Each sub-agent should receive checkpoint context
        assert len(captured_messages) == 2
        for messages in captured_messages:
            system_msg = messages[0]
            assert "Checkpoint A" in system_msg["content"]

    @pytest.mark.asyncio
    async def test_handles_sub_agent_failure(self, stuck_state):
        call_count = 0

        async def flaky_call(messages, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("API error")
            return LLMResponse(
                content="suggestion",
                input_tokens=100,
                output_tokens=50,
                model="openai/gpt-4o",
                finish_reason="stop",
            )

        mock_llm = MagicMock()
        mock_llm.call = flaky_call
        mock_llm.count_tokens = MagicMock(return_value=150)

        node = SubAgentSpawnerNode(sub_agent_count=3)
        result = await node.process(stuck_state, mock_llm)

        # Should have 2 successes and 1 failure
        assert len(result["sub_agent_results"]) == 3
        successes = [r for r in result["sub_agent_results"] if r["success"]]
        failures = [r for r in result["sub_agent_results"] if not r["success"]]
        assert len(successes) == 2
        assert len(failures) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```powershell
pytest tests/unit/test_sub_agent_spawner.py -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement sub-agent spawner**

`src/harness/plugins/sub_agent_spawner.py`:
```python
"""Parallel sub-agent spawning plugin."""

import asyncio
import logging

from harness.plugins import register_node
from harness.plugins.base import BaseNode
from harness.state import HarnessState
from harness.llm.client import LLMClient

logger = logging.getLogger(__name__)


@register_node("sub_agent_spawner")
class SubAgentSpawnerNode(BaseNode):
    """Spawns parallel sub-agents to explore solutions when stuck."""

    name = "sub_agent_spawner"

    def __init__(self, sub_agent_count: int = 3):
        self._count = sub_agent_count

    async def process(self, state: HarnessState, llm: LLMClient) -> HarnessState:
        """Spawn N sub-agents in parallel, each exploring a different approach.

        Each sub-agent receives the checkpoints and current blocker,
        and proposes a solution.
        """
        blocker = state["current_response"]
        checkpoints = state["checkpoints"]

        tasks = [
            self._run_sub_agent(i, checkpoints, blocker, llm)
            for i in range(self._count)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Normalize results
        sub_agent_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Sub-agent {i} failed: {result}")
                sub_agent_results.append({
                    "agent_id": i,
                    "success": False,
                    "content": str(result),
                    "approach": f"approach_{i}",
                })
            else:
                sub_agent_results.append(result)

        state["sub_agent_results"] = sub_agent_results
        return state

    async def _run_sub_agent(
        self,
        agent_id: int,
        checkpoints: list[str],
        blocker: str,
        llm: LLMClient,
    ) -> dict:
        """Run a single sub-agent."""
        # Build context for the sub-agent
        checkpoint_text = "\n".join(
            f"[Checkpoint {chr(65 + i)}]: {cp}"
            for i, cp in enumerate(checkpoints)
        )

        approach_prompts = [
            "Investigate clearing GPU/CUDA caches and memory pools.",
            "Check for unused parameters, dangling tensors, or detached variables.",
            "Look for circular references, event hooks, or logging that retains objects.",
        ]
        approach = approach_prompts[agent_id % len(approach_prompts)]

        messages = [
            {
                "role": "system",
                "content": (
                    f"You are sub-agent #{agent_id} exploring a specific approach.\n\n"
                    f"Reasoning context:\n{checkpoint_text}\n\n"
                    f"Your assigned approach: {approach}\n\n"
                    "Propose a concrete solution. Be specific and actionable."
                ),
            },
            {
                "role": "user",
                "content": f"The main agent is stuck on this: {blocker}\n\nWhat is your proposed solution?",
            },
        ]

        response = await llm.call(messages)

        return {
            "agent_id": agent_id,
            "success": True,
            "content": response.content,
            "approach": approach,
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```powershell
pytest tests/unit/test_sub_agent_spawner.py -v
```
Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/harness/plugins/sub_agent_spawner.py tests/unit/test_sub_agent_spawner.py
git commit -m "feat: SubAgentSpawner with parallel async execution"
```

---

## Task 9: Compactor Plugin

**Files:**
- Create: `src/harness/plugins/compactor.py`
- Create: `tests/unit/test_compactor.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_compactor.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.plugins.compactor import CompactorNode
from harness.llm.client import LLMResponse
from harness.state import HarnessState


@pytest.fixture
def state_with_sub_agent_results():
    return HarnessState(
        checkpoints=["Checkpoint A: debugging memory leak"],
        working_buffer=[
            {"role": "user", "content": "Fix the memory leak"},
            {"role": "assistant", "content": "I'm stuck."},
        ],
        is_stuck=True,
        sub_agent_results=[
            {
                "agent_id": 0,
                "success": True,
                "content": "Try clearing CUDA cache with torch.cuda.empty_cache() after each batch.",
                "approach": "Investigate clearing GPU/CUDA caches",
            },
            {
                "agent_id": 1,
                "success": True,
                "content": "Set find_unused_parameters=False in DDP and use static_graph=True.",
                "approach": "Check for unused parameters",
            },
            {
                "agent_id": 2,
                "success": False,
                "content": "API error",
                "approach": "Check circular references",
            },
        ],
        current_response="I'm stuck.",
        trace_id="test-123",
        iteration=1,
        max_iterations=5,
        metadata={},
    )


def make_mock_llm(compacted_text: str):
    mock_llm = MagicMock()
    mock_llm.call = AsyncMock(
        return_value=LLMResponse(
            content=compacted_text,
            input_tokens=200,
            output_tokens=100,
            model="openai/gpt-4o",
            finish_reason="stop",
        )
    )
    mock_llm.count_tokens = MagicMock(return_value=300)
    return mock_llm


class TestCompactorNode:
    @pytest.mark.asyncio
    async def test_creates_checkpoint_from_sub_agent_results(self, state_with_sub_agent_results):
        compacted = (
            "Derivation: DDP with unused parameters causes memory retention.\n"
            "Fix: Set find_unused_parameters=False and use static_graph=True.\n"
            "Also clear CUDA cache after each batch with torch.cuda.empty_cache()."
        )
        mock_llm = make_mock_llm(compacted)

        node = CompactorNode()
        result = await node.process(state_with_sub_agent_results, mock_llm)

        assert len(result["checkpoints"]) == 2
        assert result["checkpoints"][1] == compacted
        assert result["sub_agent_results"] == []
        assert result["is_stuck"] is False

    @pytest.mark.asyncio
    async def test_skips_when_no_results(self):
        state = HarnessState(
            checkpoints=["Checkpoint A"],
            working_buffer=[{"role": "user", "content": "test"}],
            is_stuck=False,
            sub_agent_results=[],
            current_response="",
            trace_id="test-123",
            iteration=0,
            max_iterations=5,
            metadata={},
        )
        mock_llm = MagicMock()

        node = CompactorNode()
        result = await node.process(state, mock_llm)

        assert len(result["checkpoints"]) == 1  # No new checkpoint

    @pytest.mark.asyncio
    async def test_filters_failed_sub_agents(self, state_with_sub_agent_results):
        captured_messages = []

        async def capture_call(messages, **kwargs):
            captured_messages.append(messages)
            return LLMResponse(
                content="compacted",
                input_tokens=200,
                output_tokens=100,
                model="openai/gpt-4o",
                finish_reason="stop",
            )

        mock_llm = MagicMock()
        mock_llm.call = capture_call
        mock_llm.count_tokens = MagicMock(return_value=300)

        node = CompactorNode()
        await node.process(state_with_sub_agent_results, mock_llm)

        # The compactor prompt should only include successful results
        prompt = captured_messages[0][0]["content"]
        assert "API error" not in prompt
        assert "CUDA cache" in prompt or "find_unused_parameters" in prompt
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```powershell
pytest tests/unit/test_compactor.py -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement compactor**

`src/harness/plugins/compactor.py`:
```python
"""Lean-style compaction plugin."""

import logging

from harness.plugins import register_node
from harness.plugins.base import BaseNode
from harness.state import HarnessState
from harness.llm.client import LLMClient

logger = logging.getLogger(__name__)


@register_node("compactor")
class CompactorNode(BaseNode):
    """Compacts sub-agent results into a verified logical checkpoint."""

    name = "compactor"

    async def process(self, state: HarnessState, llm: LLMClient) -> HarnessState:
        """Compact successful sub-agent results into a new checkpoint.

        Uses Chain-of-Verification prompting to extract only logically
        sound derivations from sub-agent outputs.
        """
        sub_results = state.get("sub_agent_results", [])
        if not sub_results:
            return state

        # Filter to only successful sub-agent results
        successful = [r for r in sub_results if r.get("success")]
        if not successful:
            logger.warning("All sub-agents failed, skipping compaction")
            state["sub_agent_results"] = []
            return state

        # Build compaction prompt
        agent_outputs = "\n\n".join(
            f"--- Sub-agent #{r['agent_id']} (approach: {r['approach']}) ---\n{r['content']}"
            for r in successful
        )

        checkpoint_context = "\n".join(
            f"[Checkpoint {chr(65 + i)}]: {cp}"
            for i, cp in enumerate(state["checkpoints"])
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a logical proof compactor. Your job is to extract ONLY "
                    "verified, logically sound derivations from the following outputs.\n\n"
                    "Format your response as:\n"
                    "Premise: [what we know]\n"
                    "Step: [logical derivation]\n"
                    "Conclusion: [verified finding]\n\n"
                    "Discard all conversational filler, failed attempts, hallucinations, "
                    "and unverified claims. Output ONLY the compiled takeaway."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Existing reasoning context:\n{checkpoint_context}\n\n"
                    f"Sub-agent outputs to compact:\n{agent_outputs}\n\n"
                    "Extract the verified logical derivations and create a checkpoint."
                ),
            },
        ]

        response = await llm.call(messages)

        # Create new checkpoint and update state
        state["checkpoints"].append(response.content)
        state["sub_agent_results"] = []
        state["is_stuck"] = False

        return state
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```powershell
pytest tests/unit/test_compactor.py -v
```
Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/harness/plugins/compactor.py tests/unit/test_compactor.py
git commit -m "feat: CompactorNode with Chain-of-Verification compaction"
```

---

## Task 10: Context Manager Plugin

**Files:**
- Create: `src/harness/plugins/context_manager.py`
- Create: `tests/unit/test_context_manager.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_context_manager.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.plugins.context_manager import ContextManagerNode
from harness.llm.client import LLMResponse
from harness.state import HarnessState


def make_state(
    checkpoints: list[str] | None = None,
    working_buffer: list[dict] | None = None,
) -> HarnessState:
    return HarnessState(
        checkpoints=checkpoints or [],
        working_buffer=working_buffer or [{"role": "user", "content": "test"}],
        is_stuck=False,
        sub_agent_results=[],
        current_response="",
        trace_id="test-123",
        iteration=0,
        max_iterations=5,
        metadata={},
    )


def make_mock_llm(token_count: int = 100, compacted_text: str = "compacted checkpoint"):
    mock_llm = MagicMock()
    mock_llm.count_tokens = MagicMock(return_value=token_count)
    mock_llm.call = AsyncMock(
        return_value=LLMResponse(
            content=compacted_text,
            input_tokens=200,
            output_tokens=100,
            model="openai/gpt-4o",
            finish_reason="stop",
        )
    )
    return mock_llm


class TestContextManagerNode:
    @pytest.mark.asyncio
    async def test_no_compaction_when_under_threshold(self):
        state = make_state(
            checkpoints=["short checkpoint"],
            working_buffer=[{"role": "user", "content": "hello"}],
        )
        mock_llm = make_mock_llm(token_count=100)

        node = ContextManagerNode(
            working_buffer_threshold=4000,
            full_compaction_threshold=12000,
        )
        result = await node.process(state, mock_llm)

        assert len(result["checkpoints"]) == 1
        assert result["metadata"]["compaction_type"] is None
        mock_llm.call.assert_not_called()

    @pytest.mark.asyncio
    async def test_working_buffer_compaction_performed(self):
        large_buffer = [{"role": "assistant", "content": "x" * 5000}]
        state = make_state(
            checkpoints=["checkpoint A"],
            working_buffer=large_buffer,
        )
        mock_llm = make_mock_llm(
            token_count=5000,
            compacted_text="Compacted: key finding from buffer"
        )

        node = ContextManagerNode(
            working_buffer_threshold=4000,
            full_compaction_threshold=12000,
        )
        result = await node.process(state, mock_llm)

        assert result["metadata"]["compaction_type"] == "working_buffer"
        assert len(result["checkpoints"]) == 2
        assert result["checkpoints"][1] == "Compacted: key finding from buffer"
        mock_llm.call.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_compaction_performed(self):
        checkpoints = [f"checkpoint_{i}" for i in range(20)]
        large_buffer = [{"role": "assistant", "content": "x" * 3000}]
        state = make_state(
            checkpoints=checkpoints,
            working_buffer=large_buffer,
        )
        mock_llm = make_mock_llm(
            token_count=15000,
            compacted_text="Full derivation: all findings combined"
        )

        node = ContextManagerNode(
            working_buffer_threshold=4000,
            full_compaction_threshold=12000,
        )
        result = await node.process(state, mock_llm)

        assert result["metadata"]["compaction_type"] == "full"
        assert len(result["checkpoints"]) == 1
        assert result["checkpoints"][0] == "Full derivation: all findings combined"

    @pytest.mark.asyncio
    async def test_iteration_increment(self):
        state = make_state()
        state["iteration"] = 2
        mock_llm = make_mock_llm(token_count=100)

        node = ContextManagerNode(
            working_buffer_threshold=4000,
            full_compaction_threshold=12000,
        )
        result = await node.process(state, mock_llm)

        assert result["iteration"] == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```powershell
pytest tests/unit/test_context_manager.py -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement context manager**

`src/harness/plugins/context_manager.py`:
```python
"""Context window management plugin with two-tier compaction."""

import logging

from harness.plugins import register_node
from harness.plugins.base import BaseNode
from harness.state import HarnessState
from harness.llm.client import LLMClient

logger = logging.getLogger(__name__)


@register_node("context_manager")
class ContextManagerNode(BaseNode):
    """Manages context window size with two-tier compaction.

    Tier 1: Working buffer compaction (buffer → checkpoint)
    Tier 2: Full compaction (all checkpoints + buffer → single derivation)

    Performs compaction directly using the LLM client.
    """

    name = "context_manager"

    def __init__(
        self,
        working_buffer_threshold: int = 4000,
        full_compaction_threshold: int = 12000,
    ):
        self._wb_threshold = working_buffer_threshold
        self._full_threshold = full_compaction_threshold

    async def process(self, state: HarnessState, llm: LLMClient) -> HarnessState:
        """Check context size and perform compaction if needed.

        Also increments the iteration counter.
        """
        state["iteration"] = state.get("iteration", 0) + 1

        # Count total tokens
        all_messages = self._get_all_messages(state)
        total_tokens = llm.count_tokens(all_messages)

        # Tier 2: Full compaction (highest priority)
        if total_tokens > self._full_threshold:
            logger.info(
                f"Full compaction triggered: {total_tokens} > {self._full_threshold} tokens"
            )
            state = await self._perform_full_compaction(state, llm)
            return state

        # Tier 1: Working buffer compaction
        wb_tokens = llm.count_tokens(state["working_buffer"])
        if wb_tokens > self._wb_threshold:
            logger.info(
                f"Working buffer compaction triggered: {wb_tokens} > {self._wb_threshold} tokens"
            )
            state = await self._perform_wb_compaction(state, llm)
            return state

        state["metadata"]["compaction_type"] = None
        return state

    def _get_all_messages(self, state: HarnessState) -> list[dict]:
        """Get all messages for token counting."""
        checkpoint_text = "\n".join(state["checkpoints"])
        messages = [{"role": "system", "content": checkpoint_text}]
        messages.extend(state["working_buffer"])
        return messages

    async def _perform_wb_compaction(
        self, state: HarnessState, llm: LLMClient
    ) -> HarnessState:
        """Compact working buffer into a new checkpoint."""
        checkpoint_text = "\n".join(
            f"[Checkpoint {chr(65 + i)}]: {cp}"
            for i, cp in enumerate(state["checkpoints"])
        )
        buffer_text = "\n".join(
            f"[{m['role']}]: {m['content']}" for m in state["working_buffer"]
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a context compactor. Compact the following working buffer "
                    "into a dense, verified checkpoint. Preserve all key findings, "
                    "decisions, and logical steps. Discard noise and repetition.\n\n"
                    "Format: logical derivation with Premise → Steps → Conclusion."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Existing checkpoints:\n{checkpoint_text}\n\n"
                    f"Working buffer to compact:\n{buffer_text}\n\n"
                    "Create a compact checkpoint from the working buffer."
                ),
            },
        ]

        response = await llm.call(messages)

        # Append new checkpoint, clear working buffer
        state["checkpoints"].append(response.content)
        state["working_buffer"] = [{"role": "system", "content": "Context compacted. Continue reasoning."}]
        state["metadata"]["compaction_type"] = "working_buffer"

        return state

    async def _perform_full_compaction(
        self, state: HarnessState, llm: LLMClient
    ) -> HarnessState:
        """Compact everything into a single dense derivation."""
        checkpoint_text = "\n\n".join(
            f"[Checkpoint {chr(65 + i)}]: {cp}"
            for i, cp in enumerate(state["checkpoints"])
        )
        buffer_text = "\n".join(
            f"[{m['role']}]: {m['content']}" for m in state["working_buffer"]
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a context compactor performing FULL compaction. "
                    "Combine all checkpoints and working buffer into a single, "
                    "dense, self-contained derivation. Preserve the complete "
                    "logical chain. This will become the new foundation.\n\n"
                    "Format: a single coherent derivation with all key findings."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"All checkpoints:\n{checkpoint_text}\n\n"
                    f"Working buffer:\n{buffer_text}\n\n"
                    "Create a single dense derivation from everything."
                ),
            },
        ]

        response = await llm.call(messages)

        # Reset to single checkpoint
        state["checkpoints"] = [response.content]
        state["working_buffer"] = [{"role": "system", "content": "Full compaction complete. Continue reasoning."}]
        state["metadata"]["compaction_type"] = "full"

        return state
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```powershell
pytest tests/unit/test_context_manager.py -v
```
Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/harness/plugins/context_manager.py tests/unit/test_context_manager.py
git commit -m "feat: ContextManagerNode with two-tier compaction triggers"
```

---

## Task 11: Orchestrator & Full Integration

**Files:**
- Create: `src/harness/orchestrator.py`
- Modify: `src/harness/__init__.py`
- Create: `tests/integration/test_full_cycle.py`

- [ ] **Step 1: Write failing integration test**

`tests/integration/test_full_cycle.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from harness import CognitiveHarness
from harness.config import HarnessConfig
from harness.llm.client import LLMResponse


@pytest.fixture
def config():
    return HarnessConfig(
        model="openai/gpt-4o",
        api_base="https://api.openai.com/v1",
        api_key="sk-test-123",
        max_tokens=4096,
        temperature=0.7,
        max_iterations=3,
        sub_agent_count=2,
        sub_agent_max_iterations=2,
        working_buffer_compact_threshold=4000,
        full_compaction_threshold=12000,
        stuck_detector="heuristic",
        log_level="INFO",
        jsonl_path="logs/test_traces.jsonl",
        enable_thought_tracking=True,
    )


def make_response(content: str, input_tokens: int = 100, output_tokens: int = 50):
    return LLMResponse(
        content=content,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model="openai/gpt-4o",
        finish_reason="stop",
    )


class TestCognitiveHarness:
    @pytest.mark.asyncio
    async def test_simple_non_stuck_completion(self, config):
        """Test: LLM responds without getting stuck → completes in one iteration."""
        responses = [
            make_response("The bug is on line 42. Fix: change < to <=."),
        ]

        with patch("harness.llm.client.acompletion", new_callable=AsyncMock) as mock:
            mock.side_effect = [
                _make_litellm_response(r) for r in responses
            ]
            harness = CognitiveHarness(config)
            result = await harness.invoke("Fix the off-by-one error")

        assert "line 42" in result
        assert "Fix" in result

    @pytest.mark.asyncio
    async def test_stuck_then_recover(self, config):
        """Test: LLM gets stuck, sub-agents explore, compactor produces checkpoint."""
        call_count = 0

        responses = [
            # Thinker: stuck response 1
            make_response("I think the issue is in the loop. Let me try again."),
            # Thinker: stuck response 2 (repeating)
            make_response("I think the issue is in the loop. Hmm."),
            # Thinker: stuck response 3 (hedging)
            make_response("I'm not sure. Let me try something else."),
            # Sub-agent 1
            make_response("Check find_unused_parameters in DDP."),
            # Sub-agent 2
            make_response("Try static_graph=True."),
            # Compactor
            make_response(
                "Premise: DDP with unused parameters causes memory retention.\n"
                "Step: Set find_unused_parameters=False.\n"
                "Conclusion: Use static_graph=True for fixed computation graphs."
            ),
            # Thinker: final response after recovery
            make_response("The fix is to set find_unused_parameters=False and static_graph=True."),
        ]

        with patch("harness.llm.client.acompletion", new_callable=AsyncMock) as mock:
            mock.side_effect = [
                _make_litellm_response(r) for r in responses
            ]
            harness = CognitiveHarness(config)
            result = await harness.invoke("Fix the DDP memory leak")

        assert "find_unused_parameters" in result

    @pytest.mark.asyncio
    async def test_max_iterations_safety(self, config):
        """Test: Harness stops at max_iterations even if stuck."""
        config.max_iterations = 2

        # Always return stuck-like responses
        stuck_response = make_response("I'm not sure. Let me try again.")

        with patch("harness.llm.client.acompletion", new_callable=AsyncMock) as mock:
            mock.side_effect = [
                _make_litellm_response(stuck_response) for _ in range(20)
            ]
            harness = CognitiveHarness(config)
            result = await harness.invoke("Solve an impossible problem")

        # Should return something (not hang forever)
        assert isinstance(result, str)
        assert len(result) > 0


def _make_litellm_response(resp: LLMResponse):
    """Create a mock LiteLLM response object."""
    mock = MagicMock()
    mock.choices = [MagicMock()]
    mock.choices[0].message.content = resp.content
    mock.choices[0].finish_reason = resp.finish_reason
    mock.usage.prompt_tokens = resp.input_tokens
    mock.usage.completion_tokens = resp.output_tokens
    mock.model = resp.model
    return mock
```

- [ ] **Step 2: Write failing orchestrator unit test**

`tests/unit/test_orchestrator.py`:
```python
import pytest
from harness.orchestrator import Orchestrator
from harness.config import HarnessConfig
from harness.plugins import clear_registry, register_node
from harness.plugins.base import BaseNode
from harness.state import HarnessState
from harness.llm.client import LLMClient


@pytest.fixture
def config():
    return HarnessConfig(
        model="openai/gpt-4o",
        api_base="https://api.openai.com/v1",
        api_key="sk-test",
        max_iterations=3,
    )


class TestOrchestrator:
    def setup_method(self):
        clear_registry()

    def teardown_method(self):
        clear_registry()

    def test_discovers_registered_plugins(self, config):
        @register_node("test_node")
        class TestNode(BaseNode):
            name = "test_node"

            async def process(self, state, llm):
                return state

        orch = Orchestrator(config)
        assert "test_node" in orch.available_nodes

    def test_builds_graph(self, config):
        @register_node("thinker")
        class ThinkerNode(BaseNode):
            name = "thinker"

            async def process(self, state, llm):
                return state

        @register_node("stuck_detector")
        class StuckDetectorNode(BaseNode):
            name = "stuck_detector"

            async def process(self, state, llm):
                return state

        @register_node("context_manager")
        class ContextManagerNode(BaseNode):
            name = "context_manager"

            async def process(self, state, llm):
                return state

        orch = Orchestrator(config)
        graph = orch.build_graph()
        assert graph is not None
```

- [ ] **Step 3: Run tests to verify they fail**

Run:
```powershell
pytest tests/unit/test_orchestrator.py tests/integration/test_full_cycle.py -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Implement orchestrator**

`src/harness/orchestrator.py`:
```python
"""Plugin orchestrator — builds and executes the LangGraph state graph."""

import logging
import uuid
from typing import Any

from langgraph.graph import StateGraph, END

from harness.config import HarnessConfig
from harness.llm.client import LLMClient
from harness.plugins import get_registered_nodes
from harness.plugins.base import BaseNode
from harness.state import HarnessState, create_initial_state

logger = logging.getLogger(__name__)


class Orchestrator:
    """Discovers plugins, builds the LangGraph graph, and executes it."""

    def __init__(self, config: HarnessConfig):
        self.config = config
        self.llm = LLMClient(config)
        self.available_nodes = get_registered_nodes()
        self._node_instances: dict[str, BaseNode] = {}

    def _get_node(self, name: str) -> BaseNode:
        """Get or create a plugin node instance."""
        if name not in self._node_instances:
            cls = self.available_nodes.get(name)
            if cls is None:
                raise ValueError(f"Plugin '{name}' not registered")
            self._node_instances[name] = cls()
        return self._node_instances[name]

    def build_graph(self) -> Any:
        """Build the LangGraph state graph from registered plugins.

        Graph topology:
        START → thinker → stuck_detector → [stuck path / not-stuck path]
        stuck: sub_agent_spawner → compactor → context_manager → thinker (loop)
        not-stuck: context_manager → [check iterations] → thinker (loop) or END
        """
        # Import plugin modules to trigger registration
        import harness.plugins.thinker  # noqa: F401
        import harness.plugins.stuck_detector  # noqa: F401
        import harness.plugins.sub_agent_spawner  # noqa: F401
        import harness.plugins.compactor  # noqa: F401
        import harness.plugins.context_manager  # noqa: F401

        self.available_nodes = get_registered_nodes()

        graph = StateGraph(HarnessState)

        # Add nodes
        thinker = self._make_node_wrapper("thinker")
        stuck_detector = self._make_node_wrapper("stuck_detector")
        sub_agent_spawner = self._make_node_wrapper("sub_agent_spawner")
        compactor = self._make_node_wrapper("compactor")
        context_manager = self._make_node_wrapper("context_manager")

        graph.add_node("thinker", thinker)
        graph.add_node("stuck_detector", stuck_detector)
        graph.add_node("sub_agent_spawner", sub_agent_spawner)
        graph.add_node("compactor", compactor)
        graph.add_node("context_manager", context_manager)

        # Edges
        graph.set_entry_point("thinker")
        graph.add_edge("thinker", "stuck_detector")

        # Conditional: stuck or not stuck
        graph.add_conditional_edges(
            "stuck_detector",
            self._stuck_router,
            {
                "stuck": "sub_agent_spawner",
                "not_stuck": "context_manager",
            },
        )

        graph.add_edge("sub_agent_spawner", "compactor")
        graph.add_edge("compactor", "context_manager")

        # Conditional: loop or finish
        graph.add_conditional_edges(
            "context_manager",
            self._continue_router,
            {
                "continue": "thinker",
                "finish": END,
            },
        )

        return graph.compile()

    def _make_node_wrapper(self, name: str):
        """Create an async function wrapper for a plugin node."""
        node = self._get_node(name)
        llm = self.llm

        async def wrapper(state: HarnessState) -> HarnessState:
            return await node.process(state, llm)

        return wrapper

    def _stuck_router(self, state: HarnessState) -> str:
        """Route based on stuck detection."""
        return "stuck" if state.get("is_stuck") else "not_stuck"

    def _continue_router(self, state: HarnessState) -> str:
        """Route based on iteration count and completion."""
        iteration = state.get("iteration", 0)
        max_iterations = state.get("max_iterations", 5)

        if iteration >= max_iterations:
            return "finish"

        # If not stuck after context management, we're done
        if not state.get("is_stuck"):
            return "finish"

        return "continue"

    async def invoke(self, prompt: str) -> str:
        """Execute the harness with a prompt.

        Args:
            prompt: The user's input prompt.

        Returns:
            The final response string.
        """
        trace_id = str(uuid.uuid4())
        initial_state = create_initial_state(
            trace_id=trace_id,
            max_iterations=self.config.max_iterations,
            initial_prompt=prompt,
        )

        graph = self.build_graph()
        final_state = await graph.ainvoke(initial_state)

        return final_state.get("current_response", "")
```

- [ ] **Step 5: Implement the main entry point**

`src/harness/__init__.py`:
```python
"""Cognitive LLM Harness — plugin-based reasoning engine."""

from harness.config import HarnessConfig, load_config
from harness.orchestrator import Orchestrator


class CognitiveHarness:
    """Main entry point for the cognitive harness.

    Usage:
        config = load_config("config/default.yaml")
        harness = CognitiveHarness(config)
        result = await harness.invoke("Your prompt here")
    """

    def __init__(self, config: HarnessConfig):
        self._orchestrator = Orchestrator(config)

    async def invoke(self, prompt: str) -> str:
        """Run the reasoning harness on a prompt.

        Args:
            prompt: The user's input prompt.

        Returns:
            The final response after reasoning, stuck detection,
            sub-agent exploration, and compaction.
        """
        return await self._orchestrator.invoke(prompt)


__all__ = ["CognitiveHarness", "HarnessConfig", "load_config", "Orchestrator"]
```

- [ ] **Step 6: Run unit tests**

Run:
```powershell
pytest tests/unit/test_orchestrator.py -v
```
Expected: All 2 tests PASS.

- [ ] **Step 7: Run integration tests**

Run:
```powershell
pytest tests/integration/test_full_cycle.py -v
```
Expected: All 3 tests PASS.

- [ ] **Step 8: Run all tests**

Run:
```powershell
pytest tests/ -v
```
Expected: All tests PASS.

- [ ] **Step 9: Commit**

```powershell
git add src/harness/__init__.py src/harness/orchestrator.py tests/unit/test_orchestrator.py tests/integration/test_full_cycle.py
git commit -m "feat: Orchestrator with LangGraph graph builder and CognitiveHarness entry point"
```

---

## Task 12: End-to-End Smoke Test

**Files:**
- Create: `tests/integration/test_smoke.py`

- [ ] **Step 1: Write smoke test with real LLM (optional, marked integration)**

`tests/integration/test_smoke.py`:
```python
"""End-to-end smoke test with a real LLM call.

Run with: pytest tests/integration/test_smoke.py -v -m integration
Requires: OPENAI_API_KEY environment variable set.
"""

import os
import pytest
from harness import CognitiveHarness, load_config


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)
async def test_smoke_real_llm():
    """Basic smoke test: invoke the harness with a real LLM."""
    config = load_config("config/default.yaml")
    config.max_iterations = 2  # Keep it short

    harness = CognitiveHarness(config)
    result = await harness.invoke("What is 2 + 2?")

    assert isinstance(result, str)
    assert len(result) > 0
    print(f"\nHarness response: {result}")
```

- [ ] **Step 2: Run smoke test (if API key available)**

Run:
```powershell
pytest tests/integration/test_smoke.py -v -m integration
```
Expected: PASS if OPENAI_API_KEY is set, SKIP otherwise.

- [ ] **Step 3: Commit**

```powershell
git add tests/integration/test_smoke.py
git commit -m "test: end-to-end smoke test with real LLM"
```

---

## Summary

| Task | Component | Tests |
|------|-----------|-------|
| 0 | Project setup | pytest works |
| 1 | Config | 5 unit tests |
| 2 | LLM Client | 6 unit tests |
| 3 | State | import check |
| 4 | Plugin System | 3 unit tests |
| 5 | Trace Logger | 3 unit tests |
| 6 | Thinker | 3 unit tests |
| 7 | Stuck Detector | 4 unit tests |
| 8 | Sub-Agent Spawner | 3 unit tests |
| 9 | Compactor | 3 unit tests |
| 10 | Context Manager | 4 unit tests |
| 11 | Orchestrator + Entry Point | 2 unit + 3 integration |
| 12 | Smoke Test | 1 integration (optional) |

**Total: 39 unit tests + 4 integration tests**
