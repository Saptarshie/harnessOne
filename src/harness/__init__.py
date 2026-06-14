"""Cognitive LLM Harness — plugin-based reasoning engine."""

import asyncio
import logging
from pathlib import Path
from harness.config import HarnessConfig, load_config
from harness.orchestrator import Orchestrator
from harness.session.session import Session
from harness.session.manager import SessionManager
from harness.skills.loader import SkillLoader
from harness.tools.registry import ToolRegistry
from harness.tools.builtin.file_ops import register_file_tools
from harness.tools.builtin.shell import register_shell_tool
from harness.tools.builtin.git_ops import register_git_tools
from harness.tools.builtin.search import register_search_tools
from harness.tools.builtin.web import register_web_tool
from harness.tools.builtin.skill_ops import register_skill_tools
from harness.chat.engine import ChatEngine
from harness.mcp.manager import MCPManager
from harness.improvement.tracker import PromptTracker
from harness.improvement.optimizer import PromptOptimizer
from harness.improvement.evolution import EvolutionaryEngine
from harness.memory.global_store import GlobalMemory
from harness.memory.scratchpad import Scratchpad
from harness.tracing.trace_logger import TraceLogger

logger = logging.getLogger(__name__)


class CognitiveHarness:
    """Main entry point for the cognitive harness.

    Usage:
        config = load_config("config/default.yaml")
        harness = CognitiveHarness(config)
        await harness.startup()

        session_id = await harness.start_session()
        result = await harness.chat("Fix the bug")
        result = await harness.chat("What about tests?")

        await harness.shutdown()
    """

    def __init__(self, config: HarnessConfig):
        self._config = config
        self._orchestrator = Orchestrator(config)
        self._session_manager = SessionManager(
            storage_path=config.session_storage_path,
            auto_save=config.session_auto_save,
        )
        self._skill_loader = SkillLoader(config.skills_paths)
        self._tool_registry = ToolRegistry()
        self._mcp_manager = MCPManager()
        self._session: Session | None = None
        self._chat_engine: ChatEngine | None = None

        # Self-improvement subsystems (v3.1)
        if config.improvement_enabled:
            self._tracker = PromptTracker(
                storage_path=config.tracker_storage_path,
                max_history=config.tracker_max_history,
            )
            self._optimizer = PromptOptimizer(
                tracker=self._tracker,
                min_samples=config.optimizer_min_samples,
                improvement_threshold=config.optimizer_improvement_threshold,
            )
            self._evolution = EvolutionaryEngine(
                gene_keys=["role", "constraints", "style"],
                population_size=config.evolution_population_size,
                mutation_rate=config.evolution_mutation_rate,
                crossover_rate=config.evolution_crossover_rate,
            )
        else:
            self._tracker = None
            self._optimizer = None
            self._evolution = None

        # Global memory (v3.1)
        if config.global_memory_enabled:
            self._global_memory = GlobalMemory(
                storage_path=config.global_memory_storage_path,
            )
        else:
            self._global_memory = None

        # Scratchpad (v3.1)
        if config.scratchpad_enabled:
            self._scratchpad = Scratchpad(
                max_entries=config.scratchpad_max_entries,
            )
        else:
            self._scratchpad = None

        # Trace logger (always created)
        self._trace_logger = TraceLogger(log_path=config.jsonl_path)

    async def startup(self):
        """Initialize all subsystems."""
        if self._config.skills_auto_load:
            self._skill_loader.discover()
        self._register_builtin_tools()
        await self._start_mcp_servers()

        # Load persisted state for v3.1 modules
        if self._global_memory:
            self._global_memory.load()
        if self._tracker:
            self._tracker.load()

    async def shutdown(self):
        """Clean up resources and persist state."""
        # Persist v3.1 state
        if self._global_memory:
            self._global_memory.persist()
        if self._tracker:
            self._tracker.persist()

        try:
            await self._mcp_manager.stop_all()
        except Exception:
            pass
        try:
            await self._orchestrator.shutdown_mcp_client()
        except Exception:
            pass

    def _register_builtin_tools(self):
        """Register all enabled built-in tools."""
        enabled = self._config.tools_enabled
        if "file_ops" in enabled:
            register_file_tools(self._tool_registry)
        if "shell" in enabled:
            register_shell_tool(self._tool_registry)
        if "git" in enabled:
            register_git_tools(self._tool_registry)
        if "search" in enabled:
            register_search_tools(self._tool_registry)
        if "web" in enabled:
            register_web_tool(self._tool_registry)
        if "skill_ops" in enabled:
            register_skill_tools(self._tool_registry, self._skill_loader)

    async def _start_mcp_servers(self):
        """Start configured MCP servers and register their tools."""
        servers = self._config.mcp_servers
        if not servers:
            return

        self._mcp_manager.register_from_config(servers)

        # Start each server in its own task to isolate failures
        tasks = []
        for name in self._mcp_manager.get_server_names():
            task = asyncio.create_task(self._start_single_mcp(name))
            tasks.append(task)

        # Wait for all tasks, but don't let one failure cancel others
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for name, result in zip(self._mcp_manager.get_server_names(), results):
                if isinstance(result, Exception):
                    logger.warning(f"MCP '{name}' failed: {result}")

        # Register MCP tools with the tool registry
        for tool in self._mcp_manager.get_all_tools():
            tool_name = tool["name"]
            # Avoid overwriting built-in tools
            if not self._tool_registry.has_tool(tool_name):
                self._tool_registry.register(
                    name=tool_name,
                    description=tool.get("description", ""),
                    parameters=tool.get("parameters", {}),
                    handler=self._make_mcp_handler(tool_name),
                )

    async def _start_single_mcp(self, name: str):
        """Start a single MCP server (isolated in its own task)."""
        try:
            await self._mcp_manager.start_server(name)
        except asyncio.CancelledError:
            logger.warning(f"MCP '{name}' cancelled")
            raise
        except Exception as e:
            logger.warning(f"MCP '{name}' failed: {e}")
            # Don't re-raise - let other servers continue

    def _make_mcp_handler(self, tool_name: str):
        """Create a handler function for an MCP tool."""
        async def handler(params):
            return await self._mcp_manager.call_tool(tool_name, params)
        return handler

    async def start_session(self, session_id: str = None) -> str:
        """Start a new or resume existing session."""
        if session_id:
            self._session = self._session_manager.load_session(session_id)
            if not self._session:
                raise ValueError(f"Session not found: {session_id}")
        else:
            self._session = Session()
            self._session_manager.save_session(self._session)

        # Build MCP context for system prompt
        mcp_context = self._mcp_manager.get_tools_for_prompt()

        self._chat_engine = ChatEngine(
            llm=self._orchestrator.llm,
            tool_registry=self._tool_registry,
            session=self._session,
            skill_loader=self._skill_loader,
            memory_context=mcp_context,
            tracker=self._tracker,
            scratchpad=self._scratchpad,
            global_memory=self._global_memory,
            trace_logger=self._trace_logger,
            optimizer=self._optimizer,
        )
        return self._session.id

    async def resume_session(self, session_id: str) -> str:
        """Resume an existing session."""
        return await self.start_session(session_id)

    async def chat(self, message: str, on_stream=None) -> str:
        """Send a message and get a response.

        Args:
            message: User message.
            on_stream: Optional streaming callback (delta, is_done, usage) -> None

        Returns:
            Assistant response text.
        """
        if not self._chat_engine:
            await self._start_session_if_needed()
        return await self._chat_engine.chat(message, on_stream=on_stream)

    async def _start_session_if_needed(self):
        """Start a session if one isn't active."""
        if not self._chat_engine:
            await self.start_session()

    async def list_sessions(self) -> list[dict]:
        return self._session_manager.list_sessions()

    async def list_skills(self) -> list[dict]:
        return self._skill_loader.get_all_skills()

    async def list_mcp_tools(self) -> list[dict]:
        """List all MCP tools from connected servers."""
        return self._mcp_manager.get_all_tools()

    # ── v3.1 Public API ──

    def get_improvement_report(self) -> dict:
        """Get prompt optimization report."""
        if not self._optimizer:
            return {"prompts": [], "total_metrics": 0}
        return self._optimizer.get_report()

    def get_memory_stats(self) -> dict:
        """Get global memory statistics."""
        if not self._global_memory:
            return {"total_entries": 0, "categories": {}}
        return self._global_memory.get_stats()

    def store_memory(self, key: str, content: str, category: str = "general"):
        """Store a memory entry."""
        if self._global_memory:
            self._global_memory.store(key, content, category=category)

    def retrieve_memory(self, query: str, category: str = None, limit: int = 5) -> list:
        """Retrieve memory entries matching query."""
        if not self._global_memory:
            return []
        return self._global_memory.retrieve(query, category=category, limit=limit)

    def set_scratchpad(self, label: str, content: str, priority: int = 5):
        """Set a scratchpad entry."""
        if self._scratchpad:
            self._scratchpad.set(label, content, priority=priority)

    def get_scratchpad(self, label: str) -> str | None:
        """Get a scratchpad entry."""
        if not self._scratchpad:
            return None
        return self._scratchpad.get(label)

    def clear_scratchpad(self):
        """Clear all scratchpad entries."""
        if self._scratchpad:
            self._scratchpad.clear()

    # Legacy v1/v2 interface
    async def invoke(self, prompt: str) -> str:
        """Legacy single-turn interface."""
        return await self._orchestrator.invoke(prompt)


__all__ = ["CognitiveHarness", "HarnessConfig", "load_config", "Orchestrator"]
