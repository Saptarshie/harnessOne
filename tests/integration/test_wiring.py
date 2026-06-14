"""Integration tests for v3.1 wiring — all self-improvement modules connected to live harness."""

import sys
from pathlib import Path

src_path = str(Path(__file__).parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest
import yaml
from unittest.mock import AsyncMock, MagicMock

from harness import CognitiveHarness
from harness.config import HarnessConfig, load_config
from harness.improvement.tracker import PromptTracker
from harness.improvement.optimizer import PromptOptimizer
from harness.improvement.evolution import EvolutionaryEngine
from harness.memory.global_store import GlobalMemory
from harness.memory.scratchpad import Scratchpad
from harness.tracing.trace_logger import TraceLogger


@pytest.fixture
def wiring_config(tmp_path):
    """Create a config with all v3.1 features enabled."""
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=test-key\n", encoding="utf-8")

    config = {
        "llm": {
            "model": "openai/gpt-4o",
            "api_base": "https://api.openai.com/v1",
            "api_key_env": "OPENAI_API_KEY",
        },
        "harness": {"max_iterations": 3},
        "logging": {"level": "INFO", "jsonl_path": str(tmp_path / "logs" / "traces.jsonl")},
        "memory": {"vault_path": str(tmp_path / "vault")},
        "session": {"storage_path": str(tmp_path / "sessions")},
        "skills": {"paths": []},
        "mcp_servers": [],
        "tools": {"enabled": []},
        "improvement": {
            "enabled": True,
            "tracker": {"storage_path": str(tmp_path / "metrics"), "max_history": 100},
            "optimizer": {"enabled": True, "min_samples": 5},
            "evolution": {"enabled": False},
        },
        "global_memory": {
            "enabled": True,
            "storage_path": str(tmp_path / "global_memory"),
            "max_entries": 100,
        },
        "scratchpad": {"enabled": True, "max_entries": 50},
    }

    config_file = tmp_path / "config" / "default.yaml"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(yaml.dump(config), encoding="utf-8")
    return str(config_file)


class TestCognitiveHarnessWiring:
    """Test that all v3.1 modules are wired into CognitiveHarness."""

    def test_harness_creates_tracker(self, wiring_config):
        config = load_config(wiring_config)
        harness = CognitiveHarness(config)
        assert harness._tracker is not None
        assert isinstance(harness._tracker, PromptTracker)

    def test_harness_creates_optimizer(self, wiring_config):
        config = load_config(wiring_config)
        harness = CognitiveHarness(config)
        assert harness._optimizer is not None
        assert isinstance(harness._optimizer, PromptOptimizer)

    def test_harness_creates_evolution(self, wiring_config):
        config = load_config(wiring_config)
        harness = CognitiveHarness(config)
        assert harness._evolution is not None
        assert isinstance(harness._evolution, EvolutionaryEngine)

    def test_harness_creates_global_memory(self, wiring_config):
        config = load_config(wiring_config)
        harness = CognitiveHarness(config)
        assert harness._global_memory is not None
        assert isinstance(harness._global_memory, GlobalMemory)

    def test_harness_creates_scratchpad(self, wiring_config):
        config = load_config(wiring_config)
        harness = CognitiveHarness(config)
        assert harness._scratchpad is not None
        assert isinstance(harness._scratchpad, Scratchpad)

    def test_harness_creates_trace_logger(self, wiring_config):
        config = load_config(wiring_config)
        harness = CognitiveHarness(config)
        assert harness._trace_logger is not None
        assert isinstance(harness._trace_logger, TraceLogger)

    def test_harness_disabled_when_config_off(self, tmp_path):
        """When improvement is disabled, modules are None."""
        env_file = tmp_path / ".env"
        env_file.write_text("OPENAI_API_KEY=test-key\n", encoding="utf-8")

        config = {
            "llm": {
                "model": "openai/gpt-4o",
                "api_base": "https://api.openai.com/v1",
                "api_key_env": "OPENAI_API_KEY",
            },
            "improvement": {"enabled": False},
            "global_memory": {"enabled": False},
            "scratchpad": {"enabled": False},
        }
        config_file = tmp_path / "config" / "default.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(yaml.dump(config), encoding="utf-8")

        cfg = load_config(str(config_file))
        harness = CognitiveHarness(cfg)
        assert harness._tracker is None
        assert harness._optimizer is None
        assert harness._global_memory is None
        assert harness._scratchpad is None

    @pytest.mark.asyncio
    async def test_startup_loads_global_memory(self, wiring_config, tmp_path):
        """Startup loads persisted global memory."""
        # Pre-populate global memory
        mem = GlobalMemory(str(tmp_path / "global_memory"))
        mem.store("test/key", "test content", category="test")
        mem.persist()

        config = load_config(wiring_config)
        harness = CognitiveHarness(config)
        await harness.startup()

        # Should have loaded the persisted entry
        results = harness._global_memory.retrieve("test")
        assert len(results) == 1
        assert results[0].content == "test content"

        await harness.shutdown()

    @pytest.mark.asyncio
    async def test_startup_loads_tracker_metrics(self, wiring_config, tmp_path):
        """Startup loads persisted tracker metrics."""
        from harness.improvement.tracker import PromptMetric

        tracker = PromptTracker(str(tmp_path / "metrics"))
        tracker.record(PromptMetric(
            prompt_id="sys-v1",
            prompt_text="test",
            response_text="response",
            user_message="msg",
            tokens_used=50,
            latency_ms=1000,
            tool_calls=0,
            success=True,
        ))
        tracker.persist()

        config = load_config(wiring_config)
        harness = CognitiveHarness(config)
        await harness.startup()

        assert len(harness._tracker.get_history()) == 1

        await harness.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown_persists_global_memory(self, wiring_config, tmp_path):
        """Shutdown persists global memory."""
        config = load_config(wiring_config)
        harness = CognitiveHarness(config)
        await harness.startup()

        harness._global_memory.store("new/key", "new content")
        await harness.shutdown()

        # Load fresh and verify
        mem2 = GlobalMemory(str(tmp_path / "global_memory"))
        mem2.load()
        results = mem2.retrieve("new")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_shutdown_persists_tracker(self, wiring_config, tmp_path):
        """Shutdown persists tracker metrics."""
        from harness.improvement.tracker import PromptMetric

        config = load_config(wiring_config)
        harness = CognitiveHarness(config)
        await harness.startup()

        harness._tracker.record(PromptMetric(
            prompt_id="sys-v1",
            prompt_text="test",
            response_text="response",
            user_message="msg",
            tokens_used=50,
            latency_ms=1000,
            tool_calls=0,
            success=True,
        ))
        await harness.shutdown()

        tracker2 = PromptTracker(str(tmp_path / "metrics"))
        tracker2.load()
        assert len(tracker2.get_history()) == 1


class TestChatEngineWiring:
    """Test that ChatEngine uses tracker, scratchpad, and global memory."""

    @pytest.mark.asyncio
    async def test_chat_records_metric(self, wiring_config):
        """ChatEngine records a PromptMetric after each response."""
        config = load_config(wiring_config)
        harness = CognitiveHarness(config)
        await harness.startup()

        # Mock LLM
        mock_response = MagicMock()
        mock_response.content = "Hello!"
        mock_response.tool_calls = None
        mock_response.input_tokens = 10
        mock_response.output_tokens = 5
        harness._orchestrator.llm.call_with_tools = AsyncMock(return_value=mock_response)

        session_id = await harness.start_session()
        result = await harness.chat("Hi")

        assert result == "Hello!"
        # Tracker should have recorded a metric
        assert len(harness._tracker.get_history()) == 1
        metric = harness._tracker.get_history()[0]
        assert metric.user_message == "Hi"
        assert metric.response_text == "Hello!"
        assert metric.success is True

        await harness.shutdown()

    @pytest.mark.asyncio
    async def test_chat_includes_scratchpad_context(self, wiring_config):
        """ChatEngine includes scratchpad in system prompt."""
        config = load_config(wiring_config)
        harness = CognitiveHarness(config)
        await harness.startup()

        # Set scratchpad
        harness._scratchpad.set("task", "Fix bug #123", priority=1)

        # Mock LLM
        mock_response = MagicMock()
        mock_response.content = "Fixed!"
        mock_response.tool_calls = None
        mock_response.input_tokens = 10
        mock_response.output_tokens = 5
        harness._orchestrator.llm.call_with_tools = AsyncMock(return_value=mock_response)

        session_id = await harness.start_session()
        await harness.chat("Fix the bug")

        # Verify the system prompt included scratchpad
        call_args = harness._orchestrator.llm.call_with_tools.call_args
        system_prompt = call_args.kwargs.get("system", "")
        assert "Fix bug #123" in system_prompt

        await harness.shutdown()

    @pytest.mark.asyncio
    async def test_chat_queries_global_memory(self, wiring_config):
        """ChatEngine queries global memory for relevant context."""
        config = load_config(wiring_config)
        harness = CognitiveHarness(config)
        await harness.startup()

        # Store something in global memory
        harness._global_memory.store("python/typing", "Use type hints", category="coding")

        # Mock LLM
        mock_response = MagicMock()
        mock_response.content = "Use typing module"
        mock_response.tool_calls = None
        mock_response.input_tokens = 10
        mock_response.output_tokens = 5
        harness._orchestrator.llm.call_with_tools = AsyncMock(return_value=mock_response)

        session_id = await harness.start_session()
        await harness.chat("How should I handle Python typing?")

        # Verify the system prompt included global memory context
        call_args = harness._orchestrator.llm.call_with_tools.call_args
        system_prompt = call_args.kwargs.get("system", "")
        assert "Use type hints" in system_prompt

        await harness.shutdown()


class TestHarnessImprovementAPI:
    """Test the public API for improvement operations."""

    def test_get_tracker_report(self, wiring_config):
        config = load_config(wiring_config)
        harness = CognitiveHarness(config)
        report = harness.get_improvement_report()
        assert "prompts" in report
        assert "total_metrics" in report

    def test_get_memory_stats(self, wiring_config):
        config = load_config(wiring_config)
        harness = CognitiveHarness(config)
        stats = harness.get_memory_stats()
        assert "total_entries" in stats
        assert "categories" in stats

    def test_store_memory(self, wiring_config):
        config = load_config(wiring_config)
        harness = CognitiveHarness(config)
        harness.store_memory("test/key", "test content", category="test")
        results = harness._global_memory.retrieve("test")
        assert len(results) == 1

    def test_scratchpad_operations(self, wiring_config):
        config = load_config(wiring_config)
        harness = CognitiveHarness(config)
        harness.set_scratchpad("task", "Fix bug")
        assert harness.get_scratchpad("task") == "Fix bug"
        harness.clear_scratchpad()
        assert harness.get_scratchpad("task") is None
