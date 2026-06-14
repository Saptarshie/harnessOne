"""Cognitive LLM Harness — plugin-based reasoning engine."""

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
        self._session: Session | None = None
        self._chat_engine: ChatEngine | None = None

    async def startup(self):
        """Initialize all subsystems."""
        if self._config.skills_auto_load:
            self._skill_loader.discover()
        self._register_builtin_tools()
        if self._config.vault_path:
            await self._orchestrator.start_mcp_client()

    async def shutdown(self):
        """Clean up resources."""
        await self._orchestrator.shutdown_mcp_client()

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

    async def start_session(self, session_id: str = None) -> str:
        """Start a new or resume existing session."""
        if session_id:
            self._session = self._session_manager.load_session(session_id)
            if not self._session:
                raise ValueError(f"Session not found: {session_id}")
        else:
            self._session = Session()
            self._session_manager.save_session(self._session)

        self._chat_engine = ChatEngine(
            llm=self._orchestrator.llm,
            tool_registry=self._tool_registry,
            session=self._session,
            skill_loader=self._skill_loader,
        )
        return self._session.id

    async def resume_session(self, session_id: str) -> str:
        """Resume an existing session."""
        return await self.start_session(session_id)

    async def chat(self, message: str) -> str:
        """Send a message and get a response."""
        if not self._chat_engine:
            await self.start_session()
        return await self._chat_engine.chat(message)

    async def list_sessions(self) -> list[dict]:
        return self._session_manager.list_sessions()

    async def list_skills(self) -> list[dict]:
        return self._skill_loader.get_all_skills()

    # Legacy v1/v2 interface
    async def invoke(self, prompt: str) -> str:
        """Legacy single-turn interface."""
        return await self._orchestrator.invoke(prompt)


__all__ = ["CognitiveHarness", "HarnessConfig", "load_config", "Orchestrator"]
