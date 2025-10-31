"""
测试 Skill Tool
"""

import tempfile
from pathlib import Path

import pytest

from mini_agent.tools.skill_loader import SkillLoader
from mini_agent.tools.skill_tool import GetSkillTool, ListSkillsTool, UseSkillTool


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


@pytest.fixture
def skill_loader():
    """创建包含测试 skills 的 loader"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试 skills
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
async def test_list_skills_tool(skill_loader):
    """测试 ListSkillsTool"""
    tool = ListSkillsTool(skill_loader)

    result = await tool.execute()

    assert result.success
    assert "test-skill-0" in result.content
    assert "test-skill-1" in result.content
    assert "可用的 Skills" in result.content


@pytest.mark.asyncio
async def test_list_skills_tool_empty():
    """测试空 skills 的情况"""
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = SkillLoader(tmpdir)
        loader.discover_skills()
        tool = ListSkillsTool(loader)

        result = await tool.execute()

        assert result.success
        assert "没有可用的 skills" in result.content


@pytest.mark.asyncio
async def test_get_skill_tool(skill_loader):
    """测试 GetSkillTool"""
    tool = GetSkillTool(skill_loader)

    result = await tool.execute(skill_name="test-skill-0")

    assert result.success
    assert "test-skill-0" in result.content
    assert "Test skill 0 description" in result.content
    assert "Test skill 0 content" in result.content


@pytest.mark.asyncio
async def test_get_skill_tool_nonexistent(skill_loader):
    """测试获取不存在的 skill"""
    tool = GetSkillTool(skill_loader)

    result = await tool.execute(skill_name="nonexistent-skill")

    assert not result.success
    assert "不存在" in result.error


@pytest.mark.asyncio
async def test_use_skill_tool(skill_loader):
    """测试 UseSkillTool"""
    tool = UseSkillTool(skill_loader)

    result = await tool.execute(
        skill_name="test-skill-0", task_description="Create a test document"
    )

    assert result.success
    assert "test-skill-0" in result.content
    assert "Create a test document" in result.content
    assert "Test skill 0 content" in result.content


@pytest.mark.asyncio
async def test_use_skill_tool_nonexistent(skill_loader):
    """测试使用不存在的 skill"""
    tool = UseSkillTool(skill_loader)

    result = await tool.execute(
        skill_name="nonexistent-skill", task_description="Some task"
    )

    assert not result.success
    assert "不存在" in result.error
