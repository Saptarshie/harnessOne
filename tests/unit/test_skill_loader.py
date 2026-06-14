import pytest
from pathlib import Path
from harness.skills.loader import SkillLoader


class TestSkillLoader:
    def test_discover_skills(self, tmp_path):
        skill_dir = tmp_path / "file-operations"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: file-operations\ndescription: Read and write files\n---\n\n# File Operations\n\nUse read_file and write_file tools.",
            encoding="utf-8",
        )
        loader = SkillLoader([str(tmp_path)])
        skills = loader.discover()
        assert len(skills) == 1
        assert skills[0]["name"] == "file-operations"

    def test_parse_frontmatter(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test skill\nversion: 1.0.0\nmetadata:\n  tags: [test, demo]\n---\n\n# Test\n\nContent here.",
            encoding="utf-8",
        )
        loader = SkillLoader([str(tmp_path)])
        skills = loader.discover()
        assert skills[0]["name"] == "test"
        assert "test" in skills[0]["tags"]

    def test_get_skill_content(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\ndescription: My skill\n---\n\n# My Skill\n\nDo this and that.",
            encoding="utf-8",
        )
        loader = SkillLoader([str(tmp_path)])
        loader.discover()
        content = loader.get_skill_content("my-skill")
        assert "Do this and that" in content

    def test_nested_skills(self, tmp_path):
        category = tmp_path / "software-development"
        category.mkdir()
        skill_dir = category / "tdd"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: tdd\ndescription: Test driven development\n---\n\n# TDD\n\nWrite tests first.",
            encoding="utf-8",
        )
        loader = SkillLoader([str(tmp_path)])
        skills = loader.discover()
        assert len(skills) == 1
        assert skills[0]["name"] == "tdd"

    def test_empty_skills_dir(self, tmp_path):
        loader = SkillLoader([str(tmp_path)])
        skills = loader.discover()
        assert skills == []
