import os
import pytest
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
