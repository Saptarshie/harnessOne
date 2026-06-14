"""Cognitive LLM Harness — plugin-based reasoning engine."""

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
from harness.chat.engine import ChatEngine
from harness.mcp.manager import MCPManager

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

    async def startup(self):
        """Initialize all subsystems."""
        if self._config.skills_auto_load:
            self._skill_loader.discover()
        self._register_builtin_tools()
        await self._start_mcp_servers()

    async def shutdown(self):
        """Clean up resources."""
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

    async def _start_mcp_servers(self):
        """Start configured MCP servers and register their tools."""
        servers = self._config.mcp_servers
        if not servers:
            return

        self._mcp_manager.register_from_config(servers)

        for name in self._mcp_manager.get_server_names():
            try:
                await self._mcp_manager.start_server(name)
            except Exception as e:
                logger.warning(f"Failed to start MCP server '{name}': {e}")

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
        )
        return self._session.id

    async def resume_session(self, session_id: str) -> str:
        """Resume an existing session."""
        return await self.start_session(session_id)

    async def chat(self, message: str) -> str:
        """Send a message and get a response."""
        if not self._chat_engine:
            await self._start_session_if_needed()
        return await self._chat_engine.chat(message)

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

    # Legacy v1/v2 interface
    async def invoke(self, prompt: str) -> str:
        """Legacy single-turn interface."""
        return await self._orchestrator.invoke(prompt)


__all__ = ["CognitiveHarness", "HarnessConfig", "load_config", "Orchestrator"]
