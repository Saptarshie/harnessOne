---
name: file-operations
description: Read, write, and edit files in the workspace
version: 1.0.0
metadata:
  tags: [files, io, editing, read, write]
---

# File Operations

## When to Use
When the user asks to read, create, modify, or delete files.

## Available Tools
- `read_file(path)` - Read file contents
- `write_file(path, content)` - Write content to file
- `edit_file(path, old_string, new_string)` - Edit file using string replacement

## Instructions
- Always read a file before editing it
- Use absolute paths when possible
- When editing, include enough context in old_string to make the match unique
- After writing or editing, verify the change was applied
