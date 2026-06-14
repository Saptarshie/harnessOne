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
