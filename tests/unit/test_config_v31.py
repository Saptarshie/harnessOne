"""Tests for v3.1 config fields (improvement, global_memory, scratchpad)."""

import sys
from pathlib import Path

src_path = str(Path(__file__).parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest
import yaml
from harness.config import HarnessConfig, load_config


@pytest.fixture
def full_config_file(tmp_path):
    """Create a config file with all v3.1 sections."""
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=test-key-123\n", encoding="utf-8")

    config = {
        "llm": {
            "model": "openai/gpt-4o",
            "api_base": "https://api.openai.com/v1",
            "api_key_env": "OPENAI_API_KEY",
            "max_tokens": 4096,
            "temperature": 0.7,
        },
        "harness": {
            "max_iterations": 5,
        },
        "logging": {
            "level": "INFO",
            "jsonl_path": "logs/traces.jsonl",
        },
        "memory": {
            "vault_path": "vault",
        },
        "session": {
            "storage_path": "sessions",
        },
        "skills": {
            "paths": ["skills/"],
        },
        "mcp_servers": [],
        "tools": {
            "enabled": ["file_ops", "shell"],
        },
        "api": {
            "enabled": False,
        },
        "improvement": {
            "enabled": True,
            "tracker": {
                "storage_path": ".harness/metrics",
                "max_history": 500,
            },
            "optimizer": {
                "enabled": True,
                "min_samples": 20,
                "improvement_threshold": 0.1,
            },
            "evolution": {
                "enabled": True,
                "population_size": 30,
                "generations": 15,
                "mutation_rate": 0.2,
                "crossover_rate": 0.8,
            },
        },
        "global_memory": {
            "enabled": True,
            "storage_path": ".harness/memory",
            "max_entries": 5000,
        },
        "scratchpad": {
            "enabled": True,
            "max_entries": 50,
        },
    }

    config_file = tmp_path / "config" / "default.yaml"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(yaml.dump(config), encoding="utf-8")
    return str(config_file)


class TestConfigV31:
    def test_improvement_config_loaded(self, full_config_file):
        config = load_config(full_config_file)
        assert config.improvement_enabled is True
        assert config.tracker_storage_path == ".harness/metrics"
        assert config.tracker_max_history == 500
        assert config.optimizer_enabled is True
        assert config.optimizer_min_samples == 20
        assert config.optimizer_improvement_threshold == 0.1
        assert config.evolution_enabled is True
        assert config.evolution_population_size == 30
        assert config.evolution_generations == 15
        assert config.evolution_mutation_rate == 0.2
        assert config.evolution_crossover_rate == 0.8

    def test_global_memory_config_loaded(self, full_config_file):
        config = load_config(full_config_file)
        assert config.global_memory_enabled is True
        assert config.global_memory_storage_path == ".harness/memory"
        assert config.global_memory_max_entries == 5000

    def test_scratchpad_config_loaded(self, full_config_file):
        config = load_config(full_config_file)
        assert config.scratchpad_enabled is True
        assert config.scratchpad_max_entries == 50

    def test_defaults_when_sections_missing(self, tmp_path):
        """When improvement/global_memory/scratchpad sections are missing, defaults are used."""
        env_file = tmp_path / ".env"
        env_file.write_text("OPENAI_API_KEY=test-key\n", encoding="utf-8")

        config = {
            "llm": {
                "model": "openai/gpt-4o",
                "api_base": "https://api.openai.com/v1",
                "api_key_env": "OPENAI_API_KEY",
            },
        }
        config_file = tmp_path / "config" / "default.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(yaml.dump(config), encoding="utf-8")

        cfg = load_config(str(config_file))
        # Defaults
        assert cfg.improvement_enabled is True
        assert cfg.tracker_storage_path == ".harness/prompt_metrics"
        assert cfg.tracker_max_history == 1000
        assert cfg.optimizer_min_samples == 10
        assert cfg.evolution_enabled is False
        assert cfg.global_memory_enabled is True
        assert cfg.global_memory_max_entries == 10000
        assert cfg.scratchpad_enabled is True
        assert cfg.scratchpad_max_entries == 100
