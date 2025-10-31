"""
测试 Skill Loader
"""

import tempfile
from pathlib import Path

import pytest

from mini_agent.tools.skill_loader import Skill, SkillLoader


def create_test_skill(skill_dir: Path, name: str, description: str, content: str):
    """创建测试用的 skill"""
    skill_file = skill_dir / "SKILL.md"
    skill_content = f"""---
name: {name}
description: {description}
---

{content}
"""
    skill_file.write_text(skill_content, encoding="utf-8")


def test_load_valid_skill():
    """测试加载有效的 skill"""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()

        create_test_skill(
            skill_dir,
            "test-skill",
            "A test skill",
            "This is a test skill content.",
        )

        loader = SkillLoader(tmpdir)
        skill = loader.load_skill(skill_dir / "SKILL.md")

        assert skill is not None
        assert skill.name == "test-skill"
        assert skill.description == "A test skill"
        assert "This is a test skill content" in skill.content


def test_load_skill_with_metadata():
    """测试加载包含元数据的 skill"""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()

        skill_file = skill_dir / "SKILL.md"
        skill_content = """---
name: test-skill
description: A test skill
license: MIT
allowed-tools:
  - read_file
  - write_file
metadata:
  author: Test Author
  version: "1.0"
---

Skill content here.
"""
        skill_file.write_text(skill_content, encoding="utf-8")

        loader = SkillLoader(tmpdir)
        skill = loader.load_skill(skill_file)

        assert skill is not None
        assert skill.name == "test-skill"
        assert skill.license == "MIT"
        assert skill.allowed_tools == ["read_file", "write_file"]
        assert skill.metadata["author"] == "Test Author"
        assert skill.metadata["version"] == "1.0"


def test_load_invalid_skill():
    """测试加载无效的 skill（缺少 frontmatter）"""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "invalid-skill"
        skill_dir.mkdir()

        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("No frontmatter here!", encoding="utf-8")

        loader = SkillLoader(tmpdir)
        skill = loader.load_skill(skill_file)

        assert skill is None


def test_discover_skills():
    """测试发现多个 skills"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建多个 skills
        for i in range(3):
            skill_dir = Path(tmpdir) / f"skill-{i}"
            skill_dir.mkdir()
            create_test_skill(
                skill_dir, f"skill-{i}", f"Test skill {i}", f"Content {i}"
            )

        loader = SkillLoader(tmpdir)
        skills = loader.discover_skills()

        assert len(skills) == 3
        assert len(loader.list_skills()) == 3


def test_get_skill():
    """测试获取已加载的 skill"""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()
        create_test_skill(skill_dir, "test-skill", "Test", "Content")

        loader = SkillLoader(tmpdir)
        loader.discover_skills()

        skill = loader.get_skill("test-skill")
        assert skill is not None
        assert skill.name == "test-skill"

        # 测试不存在的 skill
        assert loader.get_skill("nonexistent") is None


def test_get_skills_prompt():
    """测试生成 skills prompt"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建两个 skills
        for name in ["skill-a", "skill-b"]:
            skill_dir = Path(tmpdir) / name
            skill_dir.mkdir()
            create_test_skill(skill_dir, name, f"{name} description", f"{name} content")

        loader = SkillLoader(tmpdir)
        loader.discover_skills()

        # 测试生成所有 skills 的 prompt
        prompt = loader.get_skills_prompt()
        assert "skill-a" in prompt
        assert "skill-b" in prompt
        assert "Available Skills" in prompt

        # 测试生成特定 skills 的 prompt
        prompt = loader.get_skills_prompt(["skill-a"])
        assert "skill-a" in prompt
        assert "skill-b" not in prompt
