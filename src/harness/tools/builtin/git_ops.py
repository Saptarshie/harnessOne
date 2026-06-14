"""Git operation tools."""

import subprocess


def _run_git(args: list[str], workdir: str = None) -> str:
    try:
        result = subprocess.run(
            ["git"] + args, capture_output=True, text=True,
            timeout=30, cwd=workdir,
        )
        return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Error: {e}"


def register_git_tools(registry):
    registry.register(
        name="git_status",
        description="Show git working tree status",
        parameters={"path": {"type": "string", "description": "Repository path (optional)"}},
        handler=lambda params: _run_git(["status", "--short"], params.get("path")),
    )
    registry.register(
        name="git_diff",
        description="Show git diff",
        parameters={
            "path": {"type": "string", "description": "File path (optional)"},
            "staged": {"type": "boolean", "description": "Show staged changes"},
        },
        handler=lambda params: _run_git(
            ["diff", "--staged" if params.get("staged") == "true" else "", params.get("path", "")],
            workdir=None,
        ),
    )
    registry.register(
        name="git_log",
        description="Show recent git log",
        parameters={"count": {"type": "string", "description": "Number of entries (default: 10)"}},
        handler=lambda params: _run_git(["log", "--oneline", f"-{params.get('count', '10')}"]),
    )
