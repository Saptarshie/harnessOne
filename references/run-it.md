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
