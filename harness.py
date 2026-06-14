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
import warnings
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

# Rich imports for TUI
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich import box

console = Console()


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
        harness_root = str(HARNESS_ROOT).replace("\\", "/")
        config_content = DEFAULT_CONFIG.format(harness_root=harness_root)
        config_path.write_text(config_content, encoding="utf-8")

    return config_path


def get_env_path(cwd: str = None) -> Path:
    """Get .env path — checks CWD/.env, then .harness/.env."""
    cwd = Path(cwd or os.getcwd())

    env_file = cwd / ".env"
    if env_file.exists():
        return env_file

    harness_env = cwd / WORKSPACE_DIR / ".env"
    if harness_env.exists():
        return harness_env

    harness_env.write_text(
        "# Add your API keys here\nOPENAI_API_KEY=your-key-here\n",
        encoding="utf-8",
    )
    return harness_env


# ──────────────────────────────────────────────
# Rich TUI Helpers
# ──────────────────────────────────────────────

def banner():
    """Display startup banner."""
    console.print()
    console.print(
        Panel(
            "[bold cyan]Cognitive Harness[/bold cyan]\n"
            f"[dim]Workspace: {os.getcwd()}[/dim]",
            border_style="cyan",
            box=box.DOUBLE,
        )
    )
    console.print()


def show_status(session_id: str, context_tokens: int, max_tokens: int = 128000):
    """Display status bar with context window usage."""
    pct = min(100, int(context_tokens / max_tokens * 100))
    bar_len = 20
    filled = int(pct / 100 * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)

    # Color based on usage
    if pct < 50:
        color = "green"
    elif pct < 80:
        color = "yellow"
    else:
        color = "red"

    status = (
        f"[dim]Session:[/dim] [cyan]{session_id[:8]}[/cyan]  "
        f"[dim]Context:[/dim] [{color}]{bar} {context_tokens:,} tokens ({pct}%)[/{color}]"
    )
    console.print(f"[dim]{'─' * 60}[/dim]")
    console.print(status)
    console.print()


def show_tool_call(name: str, arguments: dict):
    """Display a tool call being executed."""
    args_str = ", ".join(f"{k}={repr(v)[:40]}" for k, v in arguments.items())
    console.print(f"  [yellow][tool][/yellow] [bold]{name}[/bold]({args_str})")


def show_tool_result(name: str, result: str):
    """Display tool execution result."""
    preview = result[:150].replace("\n", " ")
    if len(result) > 150:
        preview += "..."
    console.print(f"  [dim]  -> {preview}[/dim]")


def show_sessions(sessions: list[dict]):
    """Display sessions in a table."""
    if not sessions:
        console.print("\n[dim]No sessions found.[/dim]\n")
        return

    table = Table(title="Sessions", box=box.SIMPLE)
    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Msgs", justify="right")
    table.add_column("Last Active")

    for s in sessions:
        title = s["title"][:50] + "..." if len(s["title"]) > 50 else s["title"]
        try:
            dt = datetime.fromisoformat(s["last_active"].replace("Z", "+00:00"))
            last = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            last = s["last_active"][:16]
        table.add_row(s["id"], title, str(s["message_count"]), last)

    console.print(table)
    console.print()


def show_skills(skills: list[dict]):
    """Display available skills."""
    if not skills:
        console.print("\n[dim]No skills found.[/dim]\n")
        return

    table = Table(title="Skills", box=box.SIMPLE)
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Tags")

    for s in skills:
        tags = ", ".join(s.get("tags", []))
        table.add_row(s["name"], s["description"], tags)

    console.print(table)
    console.print()


def show_tools(tools: list[dict], mcp_tools: list[dict] = None):
    """Display available tools."""
    if not tools and not mcp_tools:
        console.print("\n[dim]No tools found.[/dim]\n")
        return

    if tools:
        table = Table(title="Built-in Tools", box=box.SIMPLE)
        table.add_column("Name", style="yellow")
        table.add_column("Parameters")
        table.add_column("Description")

        for t in tools:
            params = ", ".join(
                f"{k}: {v.get('type', 'string')}"
                for k, v in t.get("parameters", {}).items()
            )
            table.add_row(t["name"], params, t["description"][:60])

        console.print(table)

    if mcp_tools:
        table = Table(title="MCP Tools", box=box.SIMPLE)
        table.add_column("Name", style="magenta")
        table.add_column("Source")
        table.add_column("Description")

        for t in mcp_tools:
            source = t.get("source", "mcp")
            table.add_row(t["name"], source, t["description"][:60])

        console.print(table)

    console.print()


def show_help():
    """Display help."""
    console.print(
        Panel(
            "[bold]Commands:[/bold]\n"
            "  [cyan]/sessions[/cyan]         List all sessions\n"
            "  [cyan]/resume <id>[/cyan]      Resume a session\n"
            "  [cyan]/new[/cyan]              Start a new session\n"
            "  [cyan]/skills[/cyan]           List available skills\n"
            "  [cyan]/tools[/cyan]            List available tools\n"
            "  [cyan]/history[/cyan]          Show conversation history\n"
            "  [cyan]/clear[/cyan]            Clear current session\n"
            "  [cyan]/save[/cyan]             Save current session\n"
            "  [cyan]/exit[/cyan]             Save and exit\n\n"
            "[bold]Shortcuts:[/bold]\n"
            "  [dim]Ctrl+C[/dim]            Cancel current input\n"
            "  [dim]Ctrl+D[/dim]            Exit (same as /exit)",
            title="Help",
            border_style="cyan",
        )
    )


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
                console.print(f"[magenta]Resumed session: {session.id} ({len(session.messages)} messages)[/magenta]")
            except Exception as e:
                console.print(f"[red]Failed to resume session: {e}[/red]")
                self._session_id = await self._harness.start_session()
        else:
            self._session_id = await self._harness.start_session()

        # Show initial status
        self._show_context_status()
        console.print("[dim]Type your message or /help for commands.[/dim]\n")

        while self._running:
            try:
                user_input = await self._get_input()
            except (EOFError, KeyboardInterrupt):
                console.print()
                await self._do_exit()
                break

            if not user_input:
                continue

            if user_input.startswith("/"):
                await self._handle_command(user_input)
            else:
                await self._handle_message(user_input)

    def _show_context_status(self):
        """Show context window status."""
        engine = self._harness._chat_engine
        if engine:
            tokens = engine.context_tokens
            show_status(self._session_id, tokens)
        else:
            show_status(self._session_id, 0)

    async def _get_input(self) -> str:
        """Get user input with prompt."""
        try:
            line = console.input("[cyan bold]>[/cyan bold] ").strip()
            return line
        except KeyboardInterrupt:
            console.print()
            return ""

    async def _handle_message(self, message: str):
        """Process a user message through the harness with streaming."""
        try:
            # Monkey-patch tool registry for display
            original_execute = self._harness._tool_registry.execute_async

            async def traced_execute(name, params):
                show_tool_call(name, params)
                result = await original_execute(name, params)
                show_tool_result(name, result)
                return result

            self._harness._tool_registry.execute_async = traced_execute

            # Stream response
            response_text = ""
            console.print()

            async def on_stream(delta: str, is_done: bool, usage: dict | None):
                nonlocal response_text
                if delta:
                    response_text += delta
                    # Print delta in real-time (plain text)
                    sys.stdout.write(delta)
                    sys.stdout.flush()
                if is_done and usage:
                    # Final update with markdown rendering
                    pass

            response = await self._harness.chat(message, on_stream=on_stream)

            # If streaming worked, the text was already printed
            # Render final markdown version
            if response_text:
                # Clear the streamed text and re-render as markdown
                console.print()  # Newline after streaming
                console.print("[green bold]Assistant:[/green bold]")
                console.print(Markdown(response))
            else:
                console.print()
                console.print("[green bold]Assistant:[/green bold]")
                console.print(Markdown(response))

            console.print()

            # Restore original
            self._harness._tool_registry.execute_async = original_execute

            # Update context status
            self._show_context_status()

        except KeyboardInterrupt:
            console.print("\n[dim](interrupted)[/dim]")
        except Exception as e:
            console.print(f"\n[red bold]Error:[/red bold] {e}")

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
                console.print("[red]Usage: /resume <session-id>[/red]")
                return
            try:
                await self._harness.resume_session(arg)
                self._session_id = arg
                session = self._harness._session
                console.print(f"[magenta]Resumed session: {session.id}[/magenta]")
                recent = session.messages[-4:] if len(session.messages) > 4 else session.messages
                for msg in recent:
                    if msg.role == "user":
                        console.print(f"  [blue]You:[/blue] {msg.content[:80]}")
                    elif msg.role == "assistant":
                        console.print(f"  [green]Assistant:[/green] {msg.content[:80]}")
                console.print()
                self._show_context_status()
            except Exception as e:
                console.print(f"[red]Failed to resume: {e}[/red]")

        elif cmd == "/new":
            self._session_id = await self._harness.start_session()
            console.print(f"[magenta]New session: {self._session_id}[/magenta]\n")
            self._show_context_status()

        elif cmd == "/skills":
            skills = await self._harness.list_skills()
            show_skills(skills)

        elif cmd == "/tools":
            tools = self._harness._tool_registry.get_all_tools()
            mcp_tools = await self._harness.list_mcp_tools()
            show_tools(tools, mcp_tools)

        elif cmd == "/history":
            session = self._harness._session
            if not session or not session.messages:
                console.print("[dim]No messages in current session.[/dim]\n")
                return
            console.print(f"\n[bold]History ({len(session.messages)} messages):[/bold]")
            for msg in session.messages:
                if msg.role == "user":
                    console.print(f"  [blue]You:[/blue] {msg.content[:100]}")
                elif msg.role == "assistant":
                    preview = msg.content[:100] if msg.content else "(tool call)"
                    console.print(f"  [green]Assistant:[/green] {preview}")
                elif msg.role == "tool":
                    console.print(f"  [yellow]Tool [{msg.name}]:[/yellow] {msg.content[:80]}")
            console.print()

        elif cmd == "/clear":
            self._harness._session = Session()
            self._harness._session_manager.save_session(self._harness._session)
            self._session_id = self._harness._session.id
            console.print(f"[magenta]Session cleared. New session: {self._session_id}[/magenta]\n")
            self._show_context_status()

        elif cmd == "/save":
            if self._harness._session:
                self._harness._session_manager.save_session(self._harness._session)
                console.print(f"[magenta]Session saved: {self._session_id}[/magenta]\n")

        elif cmd == "/exit":
            await self._do_exit()

        else:
            console.print(f"[red]Unknown command: {cmd}. Type /help for commands.[/red]")

    async def _do_exit(self):
        """Save and exit."""
        if self._harness._session:
            self._harness._session_manager.save_session(self._harness._session)
        console.print(f"[magenta]Session saved: {self._session_id}[/magenta]")
        console.print("[dim]Goodbye![/dim]")
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
    # Suppress asyncio cleanup warnings from MCP clients
    warnings.filterwarnings("ignore", message=".*Task exception was never retrieved.*")
    warnings.filterwarnings("ignore", message=".*Attempted to exit cancel scope.*")
    warnings.filterwarnings("ignore", message=".*coroutine.*was never awaited.*")

    args = parse_args()

    # Disable colors if requested or not a terminal
    if args.no_color or not sys.stdout.isatty():
        console.no_color = True

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
        console.print(f"[green]Initialized .harness/ workspace in: {workspace.parent}[/green]")
        console.print(f"  Config: {config_path}")
        console.print(f"  Sessions: {workspace / 'sessions'}")
        console.print(f"  Vault: {workspace / 'vault'}")
        console.print(f"  Skills: {workspace / 'skills'}")
        console.print(f"  Env: {env_path}")
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
        console.print(f"[red bold]Error:[/red bold] Failed to load config: {e}")
        console.print(f"[dim]Config: {config_path}[/dim]")
        console.print(f"[dim]Edit {env_path} to set your API key.[/dim]")
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
            show_tools([], mcp_tools)
        else:
            console.print("\n[dim]No MCP servers configured. Edit .harness/config.yaml to add them.[/dim]\n")
        return

    # Startup for interactive/API modes
    async def run():
        try:
            await harness.startup()
        except asyncio.CancelledError:
            if args.verbose:
                console.print("[dim]Startup cancelled (some MCP servers may have failed)[/dim]")
        except Exception as e:
            if args.verbose:
                console.print(f"[dim]Startup warning: {e}[/dim]")

        try:
            if args.api:
                import uvicorn
                from harness.api.server import app, set_harness
                set_harness(harness)
                console.print(f"[magenta]Starting API server on {args.host}:{args.port}[/magenta]")
                console.print(f"[dim]Docs: http://{args.host}:{args.port}/docs[/dim]")
                uvicorn.run(app, host=args.host, port=args.port)
                return

            banner()
            tui = HarnessTUI(harness, session_id=args.resume)
            await tui.run()

        finally:
            # Suppress asyncio cleanup errors during shutdown
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    await harness.shutdown()
                except Exception:
                    pass

    asyncio.run(run())


if __name__ == "__main__":
    main()
