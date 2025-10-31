"""
Skill Tool - Agent 动态使用 Skills 的工具

提供给 Agent 加载和使用 Claude Skills 的能力
"""

from typing import Any, Dict, List, Optional

from .base import Tool, ToolResult
from .skill_loader import Skill, SkillLoader


class ListSkillsTool(Tool):
    """列出可用 skills 的工具"""

    def __init__(self, skill_loader: SkillLoader):
        self.skill_loader = skill_loader

    @property
    def name(self) -> str:
        return "list_skills"

    @property
    def description(self) -> str:
        return "列出所有可用的 Claude Skills，每个 skill 都是特定任务的专家指导"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def execute(self) -> ToolResult:
        """列出所有可用的 skills"""
        skills = self.skill_loader.loaded_skills.values()

        if not skills:
            return ToolResult(
                success=True,
                content="没有可用的 skills。请确保 skills 目录存在且包含有效的 SKILL.md 文件。",
            )

        # 构建 skills 列表
        skill_list = ["可用的 Skills:\n"]
        for skill in skills:
            skill_list.append(f"- **{skill.name}**: {skill.description}")

        result = "\n".join(skill_list)
        return ToolResult(success=True, content=result)


class GetSkillTool(Tool):
    """获取特定 skill 详细信息的工具"""

    def __init__(self, skill_loader: SkillLoader):
        self.skill_loader = skill_loader

    @property
    def name(self) -> str:
        return "get_skill"

    @property
    def description(self) -> str:
        return "获取指定 skill 的完整内容和指导，用于执行特定类型的任务"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "要获取的 skill 名称（使用 list_skills 查看可用的 skills）",
                }
            },
            "required": ["skill_name"],
        }

    async def execute(self, skill_name: str) -> ToolResult:
        """获取指定 skill 的详细信息"""
        skill = self.skill_loader.get_skill(skill_name)

        if not skill:
            available = ", ".join(self.skill_loader.list_skills())
            return ToolResult(
                success=False,
                content="",
                error=f"Skill '{skill_name}' 不存在。可用的 skills: {available}",
            )

        # 返回完整的 skill 内容
        result = skill.to_prompt()
        return ToolResult(success=True, content=result)


class UseSkillTool(Tool):
    """
    使用 skill 执行任务的工具

    这个工具会加载 skill 并将其指导应用到任务中
    """

    def __init__(self, skill_loader: SkillLoader):
        self.skill_loader = skill_loader

    @property
    def name(self) -> str:
        return "use_skill"

    @property
    def description(self) -> str:
        return """使用指定的 Claude Skill 来执行任务。

使用方式:
1. 先用 list_skills 查看可用的 skills
2. 用 get_skill 了解 skill 的详细指导
3. 用 use_skill 应用 skill 并说明你的任务

Skill 会提供专业的指导来完成特定类型的任务。"""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "要使用的 skill 名称",
                },
                "task_description": {
                    "type": "string",
                    "description": "任务描述，skill 将根据这个描述提供指导",
                },
            },
            "required": ["skill_name", "task_description"],
        }

    async def execute(self, skill_name: str, task_description: str) -> ToolResult:
        """使用指定的 skill"""
        skill = self.skill_loader.get_skill(skill_name)

        if not skill:
            available = ", ".join(self.skill_loader.list_skills())
            return ToolResult(
                success=False,
                content="",
                error=f"Skill '{skill_name}' 不存在。可用的 skills: {available}",
            )

        # 构建响应
        response = f"""
已加载 Skill: {skill.name}

{skill.description}

---

任务: {task_description}

---

根据 {skill.name} skill 的指导:

{skill.content}

---

请按照上述 skill 的指导完成任务。如果需要使用其他工具，请直接调用它们。
"""

        return ToolResult(success=True, content=response)


def create_skill_tools(skills_dir: str = "./skills") -> List[Tool]:
    """
    创建 skill 相关的工具

    Args:
        skills_dir: skills 目录路径

    Returns:
        工具列表
    """
    # 创建 skill loader
    loader = SkillLoader(skills_dir)

    # 发现并加载 skills
    skills = loader.discover_skills()
    print(f"✅ 发现 {len(skills)} 个 Claude Skills")

    # 创建工具
    tools = [
        ListSkillsTool(loader),
        GetSkillTool(loader),
        UseSkillTool(loader),
    ]

    return tools
