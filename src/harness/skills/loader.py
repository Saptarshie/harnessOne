"""Skill discovery and loading from SKILL.md files."""

import re
import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


class SkillLoader:
    """Discovers and loads skills from SKILL.md files."""

    def __init__(self, skill_paths: list[str]):
        self._paths = [Path(p) for p in skill_paths]
        self._skills: dict[str, dict] = {}

    def discover(self) -> list[dict]:
        """Scan skill paths for SKILL.md files."""
        self._skills = {}
        for base_path in self._paths:
            if not base_path.exists():
                continue
            for skill_file in base_path.rglob("SKILL.md"):
                skill = self._parse_skill(skill_file)
                if skill:
                    self._skills[skill["name"]] = skill
        return list(self._skills.values())

    def _parse_skill(self, file_path: Path) -> dict | None:
        """Parse a SKILL.md file with YAML frontmatter."""
        try:
            text = file_path.read_text(encoding="utf-8")
            match = re.match(r"^---\n(.*?)\n---\n\n(.*)", text, re.DOTALL)
            if not match:
                return None

            frontmatter = yaml.safe_load(match.group(1))
            content = match.group(2)

            category = frontmatter.get("category")
            if not category:
                # Try to derive from path: path is typically .../skills/<category>/<name>/SKILL.md
                # So parent.parent.name would be <category>
                if len(file_path.parts) >= 3:
                    category = file_path.parent.parent.name
                else:
                    category = "general"

            return {
                "name": frontmatter.get("name", file_path.parent.name),
                "description": frontmatter.get("description", ""),
                "version": frontmatter.get("version", "1.0.0"),
                "category": category,
                "tags": frontmatter.get("metadata", {}).get("tags", []) or frontmatter.get("metadata", {}).get("hermes", {}).get("tags", []),
                "related_skills": frontmatter.get("metadata", {}).get("related_skills", []),
                "content": content,
                "path": str(file_path),
            }
        except Exception as e:
            logger.warning(f"Failed to parse skill {file_path}: {e}")
            return None

    def get_skill_content(self, name: str) -> str:
        """Get the markdown content of a skill by name."""
        skill = self._skills.get(name)
        return skill["content"] if skill else ""

    def get_skill(self, name: str) -> dict | None:
        """Get full skill info by name."""
        return self._skills.get(name)

    def get_all_skills(self) -> list[dict]:
        """Get all discovered skills (without content, for listing)."""
        return [
            {"name": s["name"], "description": s["description"], "category": s.get("category", "general"), "tags": s["tags"]}
            for s in self._skills.values()
        ]

    def find_skills_for_task(self, task_description: str) -> list[dict]:
        """Find skills that might be relevant to a task."""
        task_lower = task_description.lower()
        matches = []
        for skill in self._skills.values():
            score = 0
            if any(tag in task_lower for tag in skill["tags"]):
                score += 2
            if any(word in skill["description"].lower() for word in task_lower.split()):
                score += 1
            if score > 0:
                matches.append((score, skill))
        matches.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in matches[:3]]
