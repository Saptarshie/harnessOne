"""
Cognitive Harness — Terminal UI Runner

Usage:
    python runner.py                    # Start new session
    python runner.py --resume <id>      # Resume session
    python runner.py --sessions         # List sessions
    python runner.py --skills           # List skills
    python runner.py --api              # Start REST API server
"""

import asyncio
import sys
import os
import argparse
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, "src")

from harness import CognitiveHarness, load_config
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
# Output Helpers
# ──────────────────────────────────────────────

def banner():
    print(f"""
{C.CYAN}{C.BOLD}============================================================
          Cognitive Harness -- Terminal Interface
============================================================{C.RESET}
""")


def print_assistant(text: str):
    """Print assistant response with formatting."""
    print(f"\n{C.GREEN}{C.BOLD}Assistant:{C.RESET}")
    # Indent each line of the response
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
    print(f"  {C.DIM}  → {preview}{C.RESET}")


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
        print(f"  {C.YELLOW}{t['name']}{C.RESET}({params}) — {t['description']}")
    print()


def show_help():
    """Display help."""
    print(f"""
{C.BOLD}Commands:{C.RESET}
  {C.CYAN}/sessions{C.RESET}         List all sessions
  {C.CYAN}/resume <id>{C.RESET}      Resume a session
  {C.CYAN}/new{C.RESET}              Start a new session
  {C.CYAN}/skills{C.RESET}           List available skills
  {C.CYAN}/tools{C.RESET}            List available tools
  {C.CYAN}/history{C.RESET}          Show conversation history
  {C.CYAN}/clear{C.RESET}            Clear current session
  {C.CYAN}/save{C.RESET}             Save current session
  {C.CYAN}/exit{C.RESET}             Save and exit

{C.BOLD}Shortcuts:{C.RESET}
  {C.DIM}Ctrl+C{C.RESET}            Cancel current input
  {C.DIM}Ctrl+D{C.RESET}            Exit (same as /exit)
  {C.DIM}Up/Down{C.RESET}           Navigate input history
""")


# ──────────────────────────────────────────────
# History
# ──────────────────────────────────────────────

class InputHistory:
    """Simple input history with up/down navigation."""

    def __init__(self):
        self._history: list[str] = []
        self._index: int = -1

    def add(self, line: str):
        if line.strip():
            self._history.append(line)
        self._index = -1

    def up(self) -> str:
        if not self._history:
            return ""
        if self._index == -1:
            self._index = len(self._history) - 1
        elif self._index > 0:
            self._index -= 1
        return self._history[self._index]

    def down(self) -> str:
        if self._index == -1:
            return ""
        if self._index < len(self._history) - 1:
            self._index += 1
            return self._history[self._index]
        self._index = -1
        return ""

    def reset(self):
        self._index = -1


# ──────────────────────────────────────────────
# Main TUI
# ──────────────────────────────────────────────

class HarnessTUI:
    """Terminal UI for the Cognitive Harness."""

    def __init__(self, harness: CognitiveHarness, session_id: str = None):
        self._harness = harness
        self._session_id = session_id
        self._running = False
        self._history = InputHistory()

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
                user_input = await self._get_input()
            except (EOFError, KeyboardInterrupt):
                print("\n")
                await self._do_exit()
                break

            if not user_input:
                continue

            self._history.add(user_input)

            if user_input.startswith("/"):
                await self._handle_command(user_input)
            else:
                await self._handle_message(user_input)

    async def _get_input(self) -> str:
        """Get user input with prompt."""
        try:
            # Use simple input() — readline support varies by platform
            line = input(f"{C.CYAN}{C.BOLD}>{C.RESET} ").strip()
            return line
        except KeyboardInterrupt:
            print()
            return ""

    async def _handle_message(self, message: str):
        """Process a user message through the harness."""
        try:
            # Monkey-patch the tool registry to show tool calls
            original_execute = self._harness._tool_registry.execute

            def traced_execute(name, params):
                print_tool_call(name, params)
                result = original_execute(name, params)
                print_tool_result(name, result)
                return result

            self._harness._tool_registry.execute = traced_execute

            response = await self._harness.chat(message)
            print_assistant(response)

            # Restore original
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
                # Show last few messages
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
            tools = self._harness._tool_registry.get_all_tools()
            show_tools(tools)

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
                elif msg.role == "system":
                    print(f"  {C.DIM}System: {msg.content[:80]}{C.RESET}")
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
        description="Cognitive Harness — Terminal Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runner.py                    Start new session
  python runner.py --resume abc-123   Resume session
  python runner.py --sessions         List all sessions
  python runner.py --skills           List available skills
  python runner.py --tools            List available tools
  python runner.py --api              Start REST API server
  python runner.py --no-color         Disable colored output
  python runner.py --config my.yaml   Use custom config
        """,
    )
    parser.add_argument("--resume", metavar="ID", help="Resume an existing session")
    parser.add_argument("--sessions", action="store_true", help="List all sessions and exit")
    parser.add_argument("--skills", action="store_true", help="List available skills and exit")
    parser.add_argument("--tools", action="store_true", help="List available tools and exit")
    parser.add_argument("--api", action="store_true", help="Start REST API server")
    parser.add_argument("--host", default="0.0.0.0", help="API host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="API port (default: 8000)")
    parser.add_argument("--config", default="config/default.yaml", help="Config file path")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

async def main():
    args = parse_args()

    # Disable colors if requested or not a terminal
    if args.no_color or not sys.stdout.isatty():
        C.disable()

    # Setup logging
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")
    else:
        import logging
        logging.basicConfig(level=logging.WARNING, format="%(message)s")

    # Load config
    try:
        config = load_config(args.config)
    except Exception as e:
        print_error(f"Failed to load config: {e}")
        sys.exit(1)

    # Create harness
    harness = CognitiveHarness(config)

    # Handle non-interactive commands (no MCP needed)
    if args.sessions:
        sessions = await harness.list_sessions()
        show_sessions(sessions)
        return

    if args.skills:
        harness._skill_loader.discover()
        skills = await harness.list_skills()
        show_skills(skills)
        return

    if args.tools:
        harness._register_builtin_tools()
        tools = harness._tool_registry.get_all_tools()
        show_tools(tools)
        return

    # Startup with MCP for interactive/API modes
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

        # Interactive mode
        banner()
        tui = HarnessTUI(harness, session_id=args.resume)
        await tui.run()

    finally:
        await harness.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
