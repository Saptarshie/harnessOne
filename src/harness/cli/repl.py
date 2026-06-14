"""Interactive CLI REPL for the harness."""


class HarnessREPL:
    """Interactive command-line interface."""

    def __init__(self, harness):
        self._harness = harness
        self._running = False

    async def run(self):
        """Start the REPL loop."""
        self._running = True
        print("Cognitive Harness v3 - Type '/help' for commands, '/exit' to quit.\n")

        while self._running:
            try:
                user_input = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            if user_input.startswith("/"):
                await self._handle_command(user_input)
            else:
                await self._handle_message(user_input)

    async def _handle_message(self, message: str):
        """Process a user message."""
        try:
            response = await self._harness.chat(message)
            print(f"\n{response}\n")
        except Exception as e:
            print(f"\nError: {e}\n")

    async def _handle_command(self, command: str):
        """Handle slash commands."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "/help":
            print("""
Commands:
  /sessions         List all sessions
  /resume <id>      Resume a session
  /new              Start a new session
  /skills           List available skills
  /tools            List available tools
  /clear            Clear current session
  /exit             Save and exit
""")
        elif cmd == "/sessions":
            sessions = await self._harness.list_sessions()
            if not sessions:
                print("No sessions found.")
            else:
                for s in sessions:
                    print(f"  {s['id']} | {s['title'][:40]} | {s['message_count']} msgs | {s['last_active'][:16]}")
        elif cmd == "/resume":
            if arg:
                await self._harness.resume_session(arg.strip())
                print(f"Resumed session {arg.strip()}")
            else:
                print("Usage: /resume <session-id>")
        elif cmd == "/new":
            sid = await self._harness.start_session()
            print(f"New session: {sid}")
        elif cmd == "/skills":
            skills = await self._harness.list_skills()
            for s in skills:
                print(f"  {s['name']}: {s['description']}")
        elif cmd == "/tools":
            tools = self._harness._tool_registry.get_all_tools()
            for t in tools:
                print(f"  {t['name']}: {t['description']}")
        elif cmd == "/clear":
            from harness.session.session import Session
            self._harness._session = Session()
            print("Session cleared.")
        elif cmd == "/exit":
            self._running = False
            print("Session saved. Goodbye!")
        else:
            print(f"Unknown command: {cmd}. Type /help for commands.")
