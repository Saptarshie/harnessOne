"""Structured JSONL execution trace logger."""

import json
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
