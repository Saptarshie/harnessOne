"""
Cognitive Harness — Terminal UI Runner

Run from any directory. Creates .harness/ in CWD for sessions, vault, etc.

Usage:
    harness                         # Start new session in CWD
    harness --resume <id>           # Resume session
    harness --sessions              # List sessions
    harness --skills                # List skills
    harness --tools                 # List tools
    harness --api                   # Start REST API server
"""

import asyncio
import sys
import os
import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding for Unicode (emojis etc.)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add harness package to path (relative to this script)
HARNESS_ROOT = Path(__file__).parent
sys.path.insert(0, str(HARNESS_ROOT / "src"))

from harness import CognitiveHarness, load_config
from harness.config import HarnessConfig
from harness.session.session import Session


# ──────────────────────────────────────────────
# ANSI Colors
# ──────────────────────────────────────────────

class C:
    """ANSI color codes."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    ITALIC  = "\033[3m"

    BLACK   = "\033[30m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"

    BG_BLACK  = "\033[40m"
    BG_RED    = "\033[41m"
    BG_GREEN  = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE   = "\033[44m"

    @staticmethod
    def disable():
        C.RESET = C.BOLD = C.DIM = C.ITALIC = ""
        C.BLACK = C.RED = C.GREEN = C.YELLOW = C.BLUE = ""
        C.MAGENTA = C.CYAN = C.WHITE = ""
        C.BG_BLACK = C.BG_RED = C.BG_GREEN = C.BG_YELLOW = C.BG_BLUE = ""


# ──────────────────────────────────────────────
# Workspace Setup
# ──────────────────────────────────────────────

WORKSPACE_DIR = ".harness"
DEFAULT_CONFIG = """\
llm:
  model: "openai/deepseek-v4-flash"
  api_base: "https://opencode.ai/zen/go/v1"
  api_key_env: "OPENAI_API_KEY"
  max_tokens: 4096
  temperature: 0.7

harness:
  max_iterations: 5
  sub_agent_count: 3
  sub_agent_max_iterations: 3
  working_buffer_compact_threshold: 4000
  full_compaction_threshold: 12000
  stuck_detector: "heuristic"

logging:
  level: "INFO"
  jsonl_path: ".harness/logs/traces.jsonl"
  enable_thought_tracking: true

memory:
  vault_path: ".harness/vault"
  embedding_model: "Qwen/Qwen3-Embedding-0.6B"
  embedding_device: "cpu"
  embedding_quantize: true
  top_k: 5
  keyword_weight: 0.4
  embedding_weight: 0.6
  mcp_server_path: "{harness_root}/mcp_server/server.py"

session:
  storage_path: ".harness/sessions"
  auto_save: true
  max_history_tokens: 100000

skills:
  paths:
    - ".harness/skills/"
    - "{harness_root}/skills/"
  auto_load: true

mcp_servers:
  # Global MCP servers are loaded from config/global-mcp.yaml
  # Add project-specific servers here (same name overrides global)
  #
  # Local (stdio):
  # - name: filesystem
  #   type: local
  #   command: npx
  #   args: ["-y", "@modelcontextprotocol/server-filesystem", "."]
  #
  # Remote (streamable_http):
  # - name: context7
  #   type: streamable_http
  #   url: https://mcp.context7.com/mcp
  []

tools:
  enabled: [file_ops, shell, git, search, web]
  shell:
    allowed_commands: []
    blocked_commands: ["rm -rf /", "format", "del /f /s /q"]
  file_ops:
    allowed_paths: ["."]
    blocked_paths: ["~/.ssh", "~/.env"]

api:
  enabled: false
  host: "0.0.0.0"
  port: 8000
"""


def get_workspace(cwd: str = None) -> Path:
    """Get or create .harness workspace in CWD."""
    workspace = Path(cwd or os.getcwd()) / WORKSPACE_DIR
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "sessions").mkdir(exist_ok=True)
    (workspace / "vault").mkdir(exist_ok=True)
    (workspace / "skills").mkdir(exist_ok=True)
    (workspace / "logs").mkdir(exist_ok=True)
    return workspace


def get_config_path(cwd: str = None) -> Path:
    """Get or create config.yaml in .harness/."""
    workspace = get_workspace(cwd)
    config_path = workspace / "config.yaml"

    if not config_path.exists():
        # Create default config with correct paths
        harness_root = str(HARNESS_ROOT).replace("\\", "/")
        config_content = DEFAULT_CONFIG.format(harness_root=harness_root)
        config_path.write_text(config_content, encoding="utf-8")

    return config_path


def get_env_path(cwd: str = None) -> Path:
    """Get .env path — checks CWD/.env, then .harness/.env."""
    cwd = Path(cwd or os.getcwd())

    # Check CWD/.env first
    env_file = cwd / ".env"
    if env_file.exists():
        return env_file

    # Check .harness/.env
    harness_env = cwd / WORKSPACE_DIR / ".env"
    if harness_env.exists():
        return harness_env

    # Create .env in .harness/ with placeholder
    harness_env.write_text(
        "# Add your API keys here\nOPENAI_API_KEY=your-key-here\n",
        encoding="utf-8",
    )
    return harness_env


# ──────────────────────────────────────────────
# Output Helpers
# ──────────────────────────────────────────────

def banner():
    cwd = os.getcwd()
    print(f"""
{C.CYAN}{C.BOLD}============================================================
          Cognitive Harness -- Terminal Interface
============================================================{C.RESET}
{C.DIM}  Workspace: {cwd}{C.RESET}
""")


def print_assistant(text: str):
    """Print assistant response with formatting."""
    print(f"\n{C.GREEN}{C.BOLD}Assistant:{C.RESET}")
    for line in text.split("\n"):
        print(f"  {line}")
    print()


def print_tool_call(name: str, arguments: dict):
    """Print a tool call being executed."""
    args_str = ", ".join(f"{k}={repr(v)[:50]}" for k, v in arguments.items())
    print(f"  {C.YELLOW}[tool] {C.BOLD}{name}{C.RESET}{C.DIM}({args_str}){C.RESET}")


def print_tool_result(name: str, result: str):
    """Print tool execution result."""
    preview = result[:200].replace("\n", " ")
    if len(result) > 200:
        preview += "..."
    print(f"  {C.DIM}  -> {preview}{C.RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"\n{C.RED}{C.BOLD}Error:{C.RESET} {text}\n")


def print_info(text: str):
    """Print info message."""
    print(f"{C.DIM}{text}{C.RESET}")


def print_system(text: str):
    """Print system message."""
    print(f"{C.MAGENTA}{text}{C.RESET}")


def format_timestamp(ts: str) -> str:
    """Format ISO timestamp to readable."""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ts[:16]


# ──────────────────────────────────────────────
# Session Display
# ──────────────────────────────────────────────

def show_sessions(sessions: list[dict]):
    """Display sessions in a table."""
    if not sessions:
        print(f"\n{C.DIM}No sessions found.{C.RESET}\n")
        return

    print(f"\n{C.BOLD}Sessions:{C.RESET}")
    print(f"  {C.DIM}{'ID':<10} {'Title':<40} {'Msgs':>5} {'Last Active':<20}{C.RESET}")
    print(f"  {C.DIM}{'-'*10} {'-'*40} {'-'*5} {'-'*20}{C.RESET}")
    for s in sessions:
        title = s["title"][:38] + ".." if len(s["title"]) > 40 else s["title"]
        last = format_timestamp(s["last_active"])
        print(f"  {C.CYAN}{s['id']:<10}{C.RESET} {title:<40} {s['message_count']:>5} {last:<20}")
    print()


def show_skills(skills: list[dict]):
    """Display available skills."""
    if not skills:
        print(f"\n{C.DIM}No skills found.{C.RESET}\n")
        return

    print(f"\n{C.BOLD}Available Skills:{C.RESET}")
    for s in skills:
        tags = ", ".join(s.get("tags", []))
        print(f"  {C.CYAN}{s['name']}{C.RESET}: {s['description']}")
        if tags:
            print(f"    {C.DIM}tags: {tags}{C.RESET}")
    print()


def show_tools(tools: list[dict]):
    """Display available tools."""
    if not tools:
        print(f"\n{C.DIM}No tools found.{C.RESET}\n")
        return

    print(f"\n{C.BOLD}Available Tools:{C.RESET}")
    for t in tools:
        params = ", ".join(
            f"{k}: {v.get('type', 'string')}"
            for k, v in t.get("parameters", {}).items()
        )
        print(f"  {C.YELLOW}{t['name']}{C.RESET}({params}) -- {t['description']}")
    print()


def show_help():
    """Display help."""
    print(f"""
{C.BOLD}Commands:{C.RESET}
  {C.CYAN}/sessions{C.RESET}         List all sessions
  {C.CYAN}/resume <id>{C.RESET}      Resume a session
  {C.CYAN}/new{C.RESET}              Start a new session
  {C.CYAN}/skills{C.RESET}           List available skills
  {C.CYAN}/tools{C.RESET}            List available tools (including MCP)
  {C.CYAN}/history{C.RESET}          Show conversation history
  {C.CYAN}/clear{C.RESET}            Clear current session
  {C.CYAN}/save{C.RESET}             Save current session
  {C.CYAN}/exit{C.RESET}             Save and exit

{C.BOLD}Shortcuts:{C.RESET}
  {C.DIM}Ctrl+C{C.RESET}            Cancel current input
  {C.DIM}Ctrl+D{C.RESET}            Exit (same as /exit)
""")


# ──────────────────────────────────────────────
# Main TUI
# ──────────────────────────────────────────────

class HarnessTUI:
    """Terminal UI for the Cognitive Harness."""

    def __init__(self, harness: CognitiveHarness, session_id: str = None):
        self._harness = harness
        self._session_id = session_id
        self._running = False

    async def run(self):
        """Main REPL loop."""
        self._running = True

        # Start or resume session
        if self._session_id:
            try:
                await self._harness.resume_session(self._session_id)
                session = self._harness._session
                print_system(f"Resumed session: {session.id} ({len(session.messages)} messages)")
            except Exception as e:
                print_error(f"Failed to resume session: {e}")
                self._session_id = await self._harness.start_session()
        else:
            self._session_id = await self._harness.start_session()

        print_info(f"Session: {self._session_id}")
        print_info("Type your message or /help for commands.\n")

        while self._running:
            try:
                user_input = input(f"{C.CYAN}{C.BOLD}>{C.RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n")
                await self._do_exit()
                break

            if not user_input:
                continue

            if user_input.startswith("/"):
                await self._handle_command(user_input)
            else:
                await self._handle_message(user_input)

    async def _handle_message(self, message: str):
        """Process a user message through the harness."""
        try:
            original_execute = self._harness._tool_registry.execute

            def traced_execute(name, params):
                print_tool_call(name, params)
                result = original_execute(name, params)
                print_tool_result(name, result)
                return result

            self._harness._tool_registry.execute = traced_execute

            response = await self._harness.chat(message)
            print_assistant(response)

            self._harness._tool_registry.execute = original_execute

        except KeyboardInterrupt:
            print(f"\n{C.DIM}(interrupted){C.RESET}")
        except Exception as e:
            print_error(str(e))

    async def _handle_command(self, command: str):
        """Handle slash commands."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd == "/help":
            show_help()

        elif cmd == "/sessions":
            sessions = await self._harness.list_sessions()
            show_sessions(sessions)

        elif cmd == "/resume":
            if not arg:
                print_error("Usage: /resume <session-id>")
                return
            try:
                await self._harness.resume_session(arg)
                self._session_id = arg
                session = self._harness._session
                print_system(f"Resumed session: {session.id}")
                recent = session.messages[-4:] if len(session.messages) > 4 else session.messages
                for msg in recent:
                    if msg.role == "user":
                        print(f"  {C.BLUE}You:{C.RESET} {msg.content[:80]}")
                    elif msg.role == "assistant":
                        print(f"  {C.GREEN}Assistant:{C.RESET} {msg.content[:80]}")
                print()
            except Exception as e:
                print_error(f"Failed to resume: {e}")

        elif cmd == "/new":
            self._session_id = await self._harness.start_session()
            print_system(f"New session: {self._session_id}\n")

        elif cmd == "/skills":
            skills = await self._harness.list_skills()
            show_skills(skills)

        elif cmd == "/tools":
            # Show built-in tools
            tools = self._harness._tool_registry.get_all_tools()
            show_tools(tools)
            # Show MCP tools if any
            mcp_tools = await self._harness.list_mcp_tools()
            if mcp_tools:
                print(f"{C.BOLD}MCP Tools:{C.RESET}")
                for t in mcp_tools:
                    source = t.get("source", "mcp")
                    print(f"  {C.MAGENTA}{t['name']}{C.RESET} -- {t['description'][:60]} {C.DIM}[{source}]{C.RESET}")
                print()

        elif cmd == "/history":
            session = self._harness._session
            if not session or not session.messages:
                print_info("No messages in current session.\n")
                return
            print(f"\n{C.BOLD}History ({len(session.messages)} messages):{C.RESET}")
            for msg in session.messages:
                if msg.role == "user":
                    print(f"  {C.BLUE}You:{C.RESET} {msg.content[:100]}")
                elif msg.role == "assistant":
                    preview = msg.content[:100] if msg.content else "(tool call)"
                    print(f"  {C.GREEN}Assistant:{C.RESET} {preview}")
                elif msg.role == "tool":
                    print(f"  {C.YELLOW}Tool [{msg.name}]:{C.RESET} {msg.content[:80]}")
            print()

        elif cmd == "/clear":
            self._harness._session = Session()
            self._harness._session_manager.save_session(self._harness._session)
            self._session_id = self._harness._session.id
            print_system(f"Session cleared. New session: {self._session_id}\n")

        elif cmd == "/save":
            if self._harness._session:
                self._harness._session_manager.save_session(self._harness._session)
                print_system(f"Session saved: {self._session_id}\n")

        elif cmd == "/exit":
            await self._do_exit()

        else:
            print_error(f"Unknown command: {cmd}. Type /help for commands.")

    async def _do_exit(self):
        """Save and exit."""
        if self._harness._session:
            self._harness._session_manager.save_session(self._harness._session)
        print_system(f"Session saved: {self._session_id}")
        print(f"{C.DIM}Goodbye!{C.RESET}")
        self._running = False


# ──────────────────────────────────────────────
# CLI Arguments
# ──────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        prog="harness",
        description="Cognitive Harness -- AI reasoning engine with tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  harness                          Start new session in current directory
  harness --resume abc-123         Resume a previous session
  harness --sessions               List all sessions
  harness --skills                 List available skills
  harness --tools                  List available tools
  harness --api                    Start REST API server
  harness --init                   Initialize .harness/ workspace

MCP Servers:
  Add MCP servers to .harness/config.yaml under mcp_servers:
    mcp_servers:
      - name: filesystem
        command: npx
        args: ["-y", "@modelcontextprotocol/server-filesystem", "."]
      - name: context7
        command: npx
        args: ["-y", "@upstash/context7-mcp"]

Workspace:
  Creates .harness/ in the current directory for:
    - sessions/    Session history (JSON)
    - vault/       Memory vault (markdown)
    - skills/      Custom skills (SKILL.md)
    - logs/        Trace logs
    - config.yaml  Configuration
        """,
    )
    parser.add_argument("--resume", metavar="ID", help="Resume an existing session")
    parser.add_argument("--sessions", action="store_true", help="List all sessions and exit")
    parser.add_argument("--skills", action="store_true", help="List available skills and exit")
    parser.add_argument("--tools", action="store_true", help="List available tools and exit")
    parser.add_argument("--mcp", action="store_true", help="List connected MCP servers and tools")
    parser.add_argument("--api", action="store_true", help="Start REST API server")
    parser.add_argument("--host", default="0.0.0.0", help="API host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="API port (default: 8000)")
    parser.add_argument("--init", action="store_true", help="Initialize .harness/ workspace and exit")
    parser.add_argument("--config", default=None, help="Custom config file path")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    args = parse_args()

    # Disable colors if requested or not a terminal
    if args.no_color or not sys.stdout.isatty():
        C.disable()

    # Setup logging
    import logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING, format="%(message)s")

    # --init: just create workspace and exit
    if args.init:
        workspace = get_workspace()
        config_path = get_config_path()
        env_path = get_env_path()
        print(f"Initialized .harness/ workspace in: {workspace.parent}")
        print(f"  Config: {config_path}")
        print(f"  Sessions: {workspace / 'sessions'}")
        print(f"  Vault: {workspace / 'vault'}")
        print(f"  Skills: {workspace / 'skills'}")
        print(f"  Env: {env_path}")
        return

    # Load or create config
    if args.config:
        config_path = Path(args.config)
    else:
        config_path = get_config_path()

    # Load .env from CWD or .harness/
    from dotenv import load_dotenv
    env_path = get_env_path()
    load_dotenv(env_path)

    try:
        config = load_config(str(config_path))
    except Exception as e:
        print_error(f"Failed to load config: {e}")
        print_info(f"Config: {config_path}")
        print_info(f"Edit {env_path} to set your API key.")
        sys.exit(1)

    # Create harness
    harness = CognitiveHarness(config)

    # Handle non-interactive commands (no startup needed)
    if args.sessions:
        sessions = asyncio.run(harness.list_sessions())
        show_sessions(sessions)
        return

    if args.skills:
        harness._skill_loader.discover()
        skills = asyncio.run(harness.list_skills())
        show_skills(skills)
        return

    if args.tools:
        harness._register_builtin_tools()
        tools = harness._tool_registry.get_all_tools()
        show_tools(tools)
        return

    if args.mcp:
        harness._register_builtin_tools()
        asyncio.run(harness._start_mcp_servers())
        mcp_tools = asyncio.run(harness.list_mcp_tools())
        if mcp_tools:
            print(f"\n{C.BOLD}MCP Servers & Tools:{C.RESET}")
            for t in mcp_tools:
                source = t.get("source", "mcp")
                print(f"  {C.MAGENTA}{t['name']}{C.RESET} -- {t['description'][:60]} {C.DIM}[{source}]{C.RESET}")
            print()
        else:
            print(f"\n{C.DIM}No MCP servers configured. Edit .harness/config.yaml to add them.{C.RESET}\n")
        return

    # Startup for interactive/API modes
    async def run():
        try:
            await harness.startup()
        except Exception as e:
            if args.verbose:
                print_info(f"Startup warning: {e}")

        try:
            if args.api:
                import uvicorn
                from harness.api.server import app, set_harness
                set_harness(harness)
                print_system(f"Starting API server on {args.host}:{args.port}")
                print_info(f"Docs: http://{args.host}:{args.port}/docs")
                uvicorn.run(app, host=args.host, port=args.port)
                return

            banner()
            tui = HarnessTUI(harness, session_id=args.resume)
            await tui.run()

        finally:
            await harness.shutdown()

    asyncio.run(run())


if __name__ == "__main__":
    main()
