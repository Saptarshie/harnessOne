"""File search tools: glob and grep."""

import re
from pathlib import Path


def register_search_tools(registry):
    def glob_search(params: dict) -> str:
        pattern = params["pattern"]
        path = params.get("path", ".")
        base = Path(path)
        if not base.exists():
            return f"Error: Path not found: {path}"
        matches = list(base.glob(pattern))
        if not matches:
            return "No files found."
        return "\n".join(str(m) for m in matches[:100])

    def grep_search(params: dict) -> str:
        pattern = params["pattern"]
        path = params.get("path", ".")
        include = params.get("include")
        base = Path(path)
        if not base.exists():
            return f"Error: Path not found: {path}"

        results = []
        try:
            regex = re.compile(pattern)
        except re.error:
            return f"Error: Invalid regex pattern: {pattern}"

        glob_pattern = include if include else "**/*"
        for file_path in base.glob(glob_pattern):
            if not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for i, line in enumerate(content.split("\n"), 1):
                    if regex.search(line):
                        results.append(f"{file_path}:{i}: {line.strip()}")
                        if len(results) >= 50:
                            return "\n".join(results) + "\n...(truncated)"
            except Exception:
                continue

        return "\n".join(results) if results else "No matches found."

    registry.register(
        name="glob",
        description="Find files matching a glob pattern",
        parameters={
            "pattern": {"type": "string", "description": "Glob pattern (e.g., '**/*.py')", "required": True},
            "path": {"type": "string", "description": "Directory to search in (default: current)"},
        },
        handler=glob_search,
    )
    registry.register(
        name="grep",
        description="Search file contents using regex",
        parameters={
            "pattern": {"type": "string", "description": "Regex pattern to search for", "required": True},
            "path": {"type": "string", "description": "Directory to search in"},
            "include": {"type": "string", "description": "File pattern to include (e.g., '*.py')"},
        },
        handler=grep_search,
    )
