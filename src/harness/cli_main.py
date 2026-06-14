"""CLI entry point for the Cognitive Harness.

Usage:
    harness                     # Start interactive session
    harness --sessions          # List sessions
    harness --skills            # List skills
    harness --tools             # List tools
    harness --mcp               # List MCP servers
    harness --init              # Initialize workspace
    harness --resume <id>       # Resume session
"""

import sys
import os
import asyncio
import warnings
import argparse
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def parse_args():
    parser = argparse.ArgumentParser(
        prog="harness",
        description="Cognitive Harness -- AI reasoning engine with tools",
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
    parser.add_argument("--config", help="Custom config file path")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


def get_workspace():
    """Get or create .harness/ workspace in CWD."""
    workspace = Path.cwd() / ".harness"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "sessions").mkdir(exist_ok=True)
    (workspace / "vault").mkdir(exist_ok=True)
    (workspace / "skills").mkdir(exist_ok=True)
    (workspace / "logs").mkdir(exist_ok=True)
    return workspace


def get_config_path():
    """Get config path: .harness/config.yaml or default."""
    local_config = Path.cwd() / ".harness" / "config.yaml"
    if local_config.exists():
        return local_config
    return None


def get_env_path():
    """Get .env path: .harness/.env or .env in CWD."""
    harness_env = Path.cwd() / ".harness" / ".env"
    if harness_env.exists():
        return harness_env
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        return cwd_env
    return harness_env


def main():
    """Main CLI entry point."""
    # Suppress asyncio cleanup warnings
    warnings.filterwarnings("ignore", message=".*Task exception was never retrieved.*")
    warnings.filterwarnings("ignore", message=".*Attempted to exit cancel scope.*")
    warnings.filterwarnings("ignore", message=".*coroutine.*was never awaited.*")

    args = parse_args()

    # Import rich for TUI
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich.markdown import Markdown
        from rich import box
    except ImportError:
        print("Error: 'rich' package required. Install with: pip install rich")
        sys.exit(1)

    console = Console()

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
        console.print(f"[green]Initialized .harness/ workspace in: {workspace.parent}[/green]")
        console.print(f"  Sessions: {workspace / 'sessions'}")
        console.print(f"  Vault: {workspace / 'vault'}")
        console.print(f"  Skills: {workspace / 'skills'}")
        return

    # Load .env
    try:
        from dotenv import load_dotenv
        env_path = get_env_path()
        if env_path:
            load_dotenv(env_path)
    except ImportError:
        pass

    # Import harness components
    try:
        from harness.config import HarnessConfig, load_config
        from harness import CognitiveHarness
        from harness.session.session import Session
        from harness.skills.loader import SkillLoader
        from harness.tools.registry import ToolRegistry
        from harness.tools.builtin.file_ops import register_file_tools
        from harness.tools.builtin.shell import register_shell_tool
        from harness.tools.builtin.git_ops import register_git_tools
        from harness.tools.builtin.search import register_search_tools
        from harness.tools.builtin.web import register_web_tool
        from harness.mcp.manager import MCPManager
    except ImportError as e:
        console.print(f"[red]Error importing harness: {e}[/red]")
        console.print("[yellow]Make sure you're in the harness project directory or run: pip install -e .[/yellow]")
        sys.exit(1)

    # Load config
    try:
        config_path = get_config_path()
        if config_path and args.config is None:
            config = load_config(str(config_path))
        elif args.config:
            config = load_config(args.config)
        else:
            config = load_config()
    except Exception as e:
        console.print(f"[red]Config error: {e}[/red]")
        sys.exit(1)

    # --sessions: list and exit
    if args.sessions:
        try:
            from harness.session.manager import SessionManager
            mgr = SessionManager(
                storage_path=config.session_storage_path,
                auto_save=config.session_auto_save,
            )
            sessions = mgr.list_sessions()
            if not sessions:
                console.print("[dim]No sessions found.[/dim]")
                return

            table = Table(title="Sessions", box=box.ROUNDED)
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Msgs", justify="right")
            table.add_column("Last Active", style="dim")

            for s in sessions:
                title = s.get("title", "")[:45]
                if len(s.get("title", "")) > 45:
                    title += "..."
                table.add_row(
                    s["id"],
                    title,
                    str(s.get("message_count", 0)),
                    s.get("last_active", "")[:19].replace("T", " "),
                )
            console.print(table)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        return

    # --skills: list and exit
    if args.skills:
        try:
            skill_loader = SkillLoader(config.skills_paths)
            skills = skill_loader.discover()
            if not skills:
                console.print("[dim]No skills found.[/dim]")
                return

            table = Table(title="Skills", box=box.ROUNDED)
            table.add_column("Name", style="cyan")
            table.add_column("Description", style="white")
            table.add_column("Tags", style="dim")

            for s in skills:
                tags = ", ".join(s.get("tags", []))
                table.add_row(s["name"], s.get("description", ""), tags)
            console.print(table)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        return

    # --tools: list and exit
    if args.tools:
        try:
            registry = ToolRegistry()
            register_file_tools(registry)
            register_shell_tool(registry)
            register_git_tools(registry)
            register_search_tools(registry)
            register_web_tool(registry)

            table = Table(title="Built-in Tools", box=box.ROUNDED)
            table.add_column("Name", style="cyan")
            table.add_column("Description", style="white")

            for tool_name in registry.get_tool_names():
                tool = registry._tools[tool_name]
                table.add_row(tool_name, tool.description)
            console.print(table)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        return

    # --mcp: list MCP servers and exit
    if args.mcp:
        try:
            mcp_manager = MCPManager()
            mcp_manager.register_from_config(config.mcp_servers or [])
            server_names = mcp_manager.get_server_names()

            if not server_names:
                console.print("[dim]No MCP servers configured.[/dim]")
                return

            table = Table(title="MCP Servers", box=box.ROUNDED)
            table.add_column("Name", style="cyan")
            table.add_column("Transport", style="white")
            table.add_column("Status", style="green")

            for name in server_names:
                server_config = mcp_manager._configs.get(name)
                if server_config:
                    table.add_row(name, server_config.transport, "configured")
            console.print(table)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        return

    # Interactive chat mode
    console.print(Panel(
        "[bold cyan]Cognitive Harness[/bold cyan]\n"
        f"Workspace: {Path.cwd()}",
        box=box.DOUBLE,
    ))

    try:
        harness = CognitiveHarness(config)

        async def run():
            await harness.startup()

            # Start session
            if args.resume:
                session_id = await harness.resume_session(args.resume)
                console.print(f"[dim]Resumed session: {session_id}[/dim]")
            else:
                session_id = await harness.start_session()
                console.print(f"[dim]Session: {session_id}[/dim]")

            console.print("\n[dim]Type your message or /help for commands. /exit to quit.[/dim]\n")

            # Chat loop
            while True:
                try:
                    user_input = console.input("[bold green]> [/bold green]")
                except (EOFError, KeyboardInterrupt):
                    break

                if not user_input.strip():
                    continue

                # Handle slash commands
                if user_input.startswith("/"):
                    cmd = user_input.strip().lower()
                    if cmd == "/exit" or cmd == "/quit":
                        break
                    elif cmd == "/help":
                        console.print(Panel(
                            "/sessions  - List sessions\n"
                            "/skills    - List skills\n"
                            "/tools     - List tools\n"
                            "/mcp       - List MCP servers\n"
                            "/clear     - Clear screen\n"
                            "/exit      - Save and exit",
                            title="Commands",
                        ))
                    elif cmd == "/sessions":
                        sessions = await harness.list_sessions()
                        for s in sessions:
                            console.print(f"  {s['id']}  {s.get('title', '')[:50]}")
                    elif cmd == "/skills":
                        skills = await harness.list_skills()
                        for s in skills:
                            console.print(f"  {s['name']}: {s.get('description', '')}")
                    elif cmd == "/clear":
                        console.clear()
                    else:
                        console.print(f"[dim]Unknown command: {cmd}[/dim]")
                    continue

                # Send message with streaming
                response_text = ""

                async def on_stream(delta, is_done, usage):
                    nonlocal response_text
                    if not is_done and delta:
                        response_text += delta
                        # Print streaming text
                        print(delta, end="", flush=True)

                try:
                    response = await harness.chat(user_input, on_stream=on_stream)
                    if response_text:
                        print()  # Newline after streaming
                    else:
                        # No streaming, print full response
                        console.print(Markdown(response))
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")

            # Shutdown
            await harness.shutdown()
            console.print("[dim]Session saved. Goodbye![/dim]")

        asyncio.run(run())

    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
