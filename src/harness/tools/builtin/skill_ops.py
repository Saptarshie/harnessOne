"""Skill operations: create_skill."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def register_skill_tools(registry, skill_loader):
    """Register skill management tools for metalearning."""

    def create_skill(params: dict) -> str:
        name = params["name"]
        description = params["description"]
        category = params.get("category", "general")
        content = params["content"]
        tags = params.get("tags", [])

        if not name or not description or not content:
            return "Error: name, description, and content are required."

        if len(description) > 1024:
            return "Error: description must be <= 1024 characters."

        # Ensure valid name (lowercase, hyphens)
        if not name.replace("-", "").isalnum() or not name.islower():
            return "Error: name must be lowercase alphanumeric with hyphens."

        # Format YAML frontmatter
        tags_yaml = ", ".join([f'"{t}"' for t in tags])
        frontmatter = f"""---
name: {name}
description: "{description}"
version: 1.0.0
author: Cognitive Harness
license: MIT
metadata:
  hermes:
    tags: [{tags_yaml}]
---
"""
        full_content = frontmatter + "\n" + content

        # We need to determine where to save it. We'll use the first path in the skill loader.
        # Typically the first is the project-local .harness/skills or skills/ folder.
        if not skill_loader._paths:
            return "Error: No skill paths configured."

        # Try to find an existing skills/ directory
        target_base = None
        for base in skill_loader._paths:
            if "skills" in str(base).lower():
                target_base = base
                break
        
        if not target_base:
            target_base = skill_loader._paths[0]

        skill_dir = target_base / category / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(full_content, encoding="utf-8")

        # Reload skills
        skill_loader.discover()

        return f"Successfully created skill '{name}' in {category}. It has been loaded and is immediately available."

    registry.register(
        name="create_skill",
        description="Create a new reusable skill to metalearn and evolve over time.",
        parameters={
            "name": {"type": "string", "description": "Lowercase, hyphenated name (e.g. 'process-logs')", "required": True},
            "description": {"type": "string", "description": "Short description of when to use it", "required": True},
            "category": {"type": "string", "description": "Category folder (e.g. 'data-science', 'software-development', 'general')", "required": True},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for skill discovery", "required": True},
            "content": {"type": "string", "description": "Markdown content for the skill instructions", "required": True},
        },
        handler=create_skill,
    )
