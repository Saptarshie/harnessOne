"""Shell command execution tool."""

import subprocess
import sys


def register_shell_tool(registry, blocked_commands=None):
    blocked = blocked_commands or []

    def run_command(params: dict) -> str:
        command = params["command"]
        workdir = params.get("workdir")
        timeout = int(params.get("timeout", 60))

        for blocked_cmd in blocked:
            if blocked_cmd in command:
                return f"Error: Command blocked: {blocked_cmd}"

        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True,
                    timeout=timeout, cwd=workdir,
                )
            else:
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True,
                    timeout=timeout, cwd=workdir,
                )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"
            if result.returncode != 0:
                output += f"\n[exit code: {result.returncode}]"
            return output[:10000]
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {timeout}s"
        except Exception as e:
            return f"Error: {e}"

    registry.register(
        name="run_command",
        description="Run a shell command",
        parameters={
            "command": {"type": "string", "description": "Command to execute", "required": True},
            "workdir": {"type": "string", "description": "Working directory (optional)"},
            "timeout": {"type": "string", "description": "Timeout in seconds (default: 60)"},
        },
        handler=run_command,
    )
