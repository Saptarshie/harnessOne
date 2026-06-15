Done — Harness works from any directory
How it works:

# From any directory:

cd /path/to/my-project
python D:\prac_prog\fun\hernessOne\harnssOne-1\harness.py

# First run creates .harness/ in CWD:

my-project/
├── .harness/
│ ├── config.yaml # Auto-generated config
│ ├── .env # API keys (edit this)
│ ├── sessions/ # Session history
│ ├── vault/ # Memory vault
│ ├── skills/ # Custom skills
│ └── logs/ # Trace logs
├── your-project-files...
Quick setup for any folder:

# Option 1: Run directly

python D:\prac_prog\fun\hernessOne\harnssOne-1\harness.py

# Option 2: Create alias (PowerShell profile)

# Add to $PROFILE:

function harness { python D:\prac_prog\fun\hernessOne\harnssOne-1\harness.py @args }

# Option 3: Add D:\prac_prog\fun\hernessOne\harnssOne-1 to PATH

# Then run: harness

Commands:
harness # Start interactive session
harness --init # Create .harness/ workspace only
harness --sessions # List sessions
harness --skills # List skills
harness --tools # List tools
harness --resume <id> # Resume session
harness --api # Start REST API
First time setup:
cd your-project
harness --init

# Edit .harness/.env with your API key

harness
Each project gets its own .harness/ workspace — sessions, vault, and skills are isolated per project.

---

How to add custom MCP servers
Edit .harness/config.yaml in your project:
mcp_servers:

# Filesystem access

- name: filesystem
  command: npx
  args: ["-y", "@modelcontextprotocol/server-filesystem", "."]

# GitHub

- name: github
  command: npx
  args: ["-y", "@modelcontextprotocol/server-github"]
  env:
  GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_TOKEN}"

# Brave Search

- name: brave-search
  command: npx
  args: ["-y", "@modelcontextprotocol/server-brave-search"]
  env:
  BRAVE_API_KEY: "${BRAVE_API_KEY}"

# Context7 (library docs)

- name: context7
  command: npx
  args: ["-y", "@upstash/context7-mcp"]

# PDF tools

- name: pdf
  command: uvx
  args: ["mcp-server-pdf"]

# Custom Python MCP server

- name: my-server
  command: python
  args: ["path/to/my_mcp_server.py"]
  Commands:
  harness --mcp # List connected MCP servers and their tools
  harness --tools # List all tools (built-in + MCP)
  harness # Start session with MCP tools available
  What happens:

1. MCP servers start on harness startup
2. Tools are auto-discovered and registered
3. LLM can call MCP tools like built-in tools
4. Tools appear in /tools and /mcp commands
   Example output:
   MCP Servers & Tools:
   read_file -- Read the complete contents of a file... [mcp:filesystem]
   write_file -- Create a new file or overwrite... [mcp:filesystem]
   list_directory -- Get detailed listing... [mcp:filesystem]
   search_files -- Recursively search for files... [mcp:filesystem]
   ...14 tools total

---

Fixed — CLI Entry Point
The harness command now works from any directory.
How to Use

# From any directory:

harness # Start interactive session
harness --sessions # List sessions
harness --skills # List skills
harness --tools # List tools
harness --mcp # List MCP servers
harness --init # Initialize .harness/ workspace
harness --resume <id> # Resume session
What Changed

1. Created src/harness/cli_main.py — CLI entry point inside the package
2. Updated pyproject.toml — entry point now harness.cli_main:main
3. Reinstalled package — pip install -e .
   Test
   PS D:\prac_prog\fun\hernessOne\test\workspace-1> harness --sessions
   Sessions  
   ┌──────────┬─────────────────────────────────────┬──────┬─────────────────────┐
   │ ID │ Title │ Msgs │ Last Active │
   ├──────────┼─────────────────────────────────────┼──────┼─────────────────────┤
   │ 407423b2 │ do research and explain me how │ 14 │ 2026-06-14 11:33 │
   │ bbce2f9a │ Hi , list all the tools and mcps │ 69 │ 2026-06-14 11:19 │
   └──────────┴─────────────────────────────────────┴──────┴─────────────────────┘
