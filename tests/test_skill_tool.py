"""
Test Skill Tool

Tests for skill tools after Progressive Disclosure optimization:
- Only GetSkillTool remains (ListSkillsTool and UseSkillTool removed)
- Tests verify the single-tool approach
"""

import tempfile
from pathlib import Path

import pytest

from ye_linghua.tools.skill_loader import SkillLoader
from ye_linghua.tools.skill_tool import GetSkillTool, create_skill_tools


def create_test_skill(skill_dir: Path, name: str, description: str, content: str):
    """Create a test skill"""
    skill_file = skill_dir / "SKILL.md"
    skill_content = f"""---
name: {name}
description: {description}
---

{content}
"""
    skill_file.write_text(skill_content, encoding="utf-8")


@pytest.fixture
def skill_loader():
    """Create a loader with test skills"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test skills
        for i in range(2):
            skill_dir = Path(tmpdir) / f"test-skill-{i}"
            skill_dir.mkdir()
            create_test_skill(
                skill_dir,
                f"test-skill-{i}",
                f"Test skill {i} description",
                f"Test skill {i} content and instructions.",
            )

        loader = SkillLoader(tmpdir)
        loader.discover_skills()
        yield loader


@pytest.mark.asyncio
async def test_get_skill_tool(skill_loader):
    """Test GetSkillTool"""
    tool = GetSkillTool(skill_loader)

    result = await tool.execute(skill_name="test-skill-0")

    assert result.success
    assert "test-skill-0" in result.content
    assert "Test skill 0 description" in result.content
    assert "Test skill 0 content" in result.content


@pytest.mark.asyncio
async def test_get_skill_tool_nonexistent(skill_loader):
    """Test getting non-existent skill"""
    tool = GetSkillTool(skill_loader)

    result = await tool.execute(skill_name="nonexistent-skill")

    assert not result.success
    assert "不存在" in result.error or "not exist" in result.error.lower()


def test_create_skill_tools_returns_single_tool(skill_loader):
    """Test that create_skill_tools only returns GetSkillTool after optimization"""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()
        create_test_skill(
            skill_dir, "test-skill", "Test skill", "Test content"
        )

        tools, loader = create_skill_tools(tmpdir)

        # Should only have one tool now (GetSkillTool)
        assert len(tools) == 1
        assert isinstance(tools[0], GetSkillTool)
        assert loader is not None


def test_tool_count_optimization():
    """Verify Progressive Disclosure optimization: 3 tools -> 1 tool"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple test skill
        skill_dir = Path(tmpdir) / "simple-skill"
        skill_dir.mkdir()
        create_test_skill(
            skill_dir, "simple-skill", "Simple test", "Content"
        )

        tools, _ = create_skill_tools(tmpdir)

        # After optimization, should only have 1 tool (GetSkillTool)
        # Before optimization, we had 3 tools (ListSkillsTool, GetSkillTool, UseSkillTool)
        assert len(tools) == 1

        # Verify it's GetSkillTool
        tool = tools[0]
        assert tool.name == "get_skill"
        assert "get complete content" in tool.description.lower() or "获取" in tool.description
