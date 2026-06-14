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
        self._mcp_client = None

    async def start_mcp_client(self):
        """Start the MCP client for memory operations."""
        if self.config.vault_path:
            from harness.memory.mcp_client import MCPClient
            self._mcp_client = MCPClient(
                server_path=self.config.mcp_server_path,
                vault_path=self.config.vault_path,
                embedding_model=self.config.embedding_model,
            )
            try:
                await self._mcp_client.start()
                logger.info("MCP client started")
            except Exception as e:
                logger.warning(f"Failed to start MCP client: {e}")
                self._mcp_client = None

    async def shutdown_mcp_client(self):
        """Shut down the MCP client."""
        if self._mcp_client:
            await self._mcp_client.shutdown()
            self._mcp_client = None

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
        START -> thinker -> stuck_detector -> [stuck path / not-stuck path]
        stuck: sub_agent_spawner -> compactor -> context_manager -> thinker (loop)
        not-stuck: context_manager -> [check iterations] -> thinker (loop) or END
        """
        # Import plugin modules to trigger registration
        import harness.plugins.thinker  # noqa: F401
        import harness.plugins.stuck_detector  # noqa: F401
        import harness.plugins.sub_agent_spawner  # noqa: F401
        import harness.plugins.compactor  # noqa: F401
        import harness.plugins.context_manager  # noqa: F401

        # Import memory plugins (v2)
        has_memory = False
        if self._mcp_client:
            try:
                import harness.plugins.memory_query  # noqa: F401
                import harness.plugins.memory_writer_node  # noqa: F401
                has_memory = True
            except ImportError:
                pass

        self.available_nodes = get_registered_nodes()

        graph = StateGraph(HarnessState)

        # Add core nodes
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

        # Add memory nodes if MCP client available
        if has_memory:
            memory_query = self._make_memory_node("memory_query")
            memory_writer = self._make_memory_node("memory_writer")
            graph.add_node("memory_query", memory_query)
            graph.add_node("memory_writer", memory_writer)

            # Wire: START -> memory_query -> thinker
            graph.set_entry_point("memory_query")
            graph.add_edge("memory_query", "thinker")

            # Wire: compactor -> memory_writer -> context_manager
            graph.add_edge("compactor", "memory_writer")
            graph.add_edge("memory_writer", "context_manager")
        else:
            # Original flow without memory
            graph.set_entry_point("thinker")
            graph.add_edge("compactor", "context_manager")

        # Edges
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

    def _make_memory_node(self, name: str):
        """Create an async function wrapper for a memory plugin node."""
        cls = self.available_nodes.get(name)
        if cls is None:
            raise ValueError(f"Memory plugin '{name}' not registered")
        node = cls(mcp_client=self._mcp_client)
        llm = self.llm

        async def wrapper(state: HarnessState) -> HarnessState:
            return await node.process(state, llm)

        return wrapper

    def _stuck_router(self, state: HarnessState) -> str:
        """Route based on stuck detection."""
        return "stuck" if state.get("is_stuck") else "not_stuck"

    def _continue_router(self, state: HarnessState) -> str:
        """Route based on iteration count and stuck status."""
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
