"""File operation tools: read_file, write_file, edit_file."""

from pathlib import Path


def register_file_tools(registry):
    """Register file operation tools."""

    def read_file(params: dict) -> str:
        path = params["path"]
        p = Path(path)
        if not p.exists():
            return f"Error: File not found: {path}"
        return p.read_text(encoding="utf-8")

    def write_file(params: dict) -> str:
        path = params["path"]
        content = params["content"]
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"File written: {path} ({len(content)} chars)"

    def edit_file(params: dict) -> str:
        path = params["path"]
        old_string = params["old_string"]
        new_string = params["new_string"]
        p = Path(path)
        if not p.exists():
            return f"Error: File not found: {path}"
        content = p.read_text(encoding="utf-8")
        if old_string not in content:
            return f"Error: old_string not found in {path}"
        count = content.count(old_string)
        if count > 1:
            return f"Error: old_string found {count} times in {path}. Provide more context."
        new_content = content.replace(old_string, new_string, 1)
        p.write_text(new_content, encoding="utf-8")
        return f"File edited: {path}"

    registry.register(
        name="read_file",
        description="Read the contents of a file",
        parameters={"path": {"type": "string", "description": "Absolute path to the file", "required": True}},
        handler=read_file,
    )
    registry.register(
        name="write_file",
        description="Write content to a file (creates parent directories)",
        parameters={
            "path": {"type": "string", "description": "Absolute path to the file", "required": True},
            "content": {"type": "string", "description": "Content to write", "required": True},
        },
        handler=write_file,
    )
    registry.register(
        name="edit_file",
        description="Edit a file by replacing old_string with new_string",
        parameters={
            "path": {"type": "string", "description": "Absolute path to the file", "required": True},
            "old_string": {"type": "string", "description": "String to replace (must be unique)", "required": True},
            "new_string": {"type": "string", "description": "Replacement string", "required": True},
        },
        handler=edit_file,
    )
