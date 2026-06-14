import json
import pytest
from harness.tracing.trace_logger import TraceLogger


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
