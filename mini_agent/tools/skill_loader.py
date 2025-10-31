"""
Skill Loader - 加载 Claude Skills

支持从 SKILL.md 文件加载 skills，并提供给 Agent 使用
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class Skill:
    """Skill 数据结构"""

    name: str
    description: str
    content: str
    license: Optional[str] = None
    allowed_tools: Optional[List[str]] = None
    metadata: Optional[Dict[str, str]] = None
    skill_path: Optional[Path] = None

    def to_prompt(self) -> str:
        """将 skill 转换为 prompt 格式"""
        return f"""
# Skill: {self.name}

{self.description}

---

{self.content}
"""


class SkillLoader:
    """Skill 加载器"""

    def __init__(self, skills_dir: str = "./skills"):
        """
        初始化 Skill Loader

        Args:
            skills_dir: skills 目录路径
        """
        self.skills_dir = Path(skills_dir)
        self.loaded_skills: Dict[str, Skill] = {}

    def load_skill(self, skill_path: Path) -> Optional[Skill]:
        """
        从 SKILL.md 文件加载单个 skill

        Args:
            skill_path: SKILL.md 文件路径

        Returns:
            Skill 对象，如果加载失败则返回 None
        """
        try:
            content = skill_path.read_text(encoding="utf-8")

            # 解析 YAML frontmatter
            frontmatter_match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)

            if not frontmatter_match:
                print(f"⚠️  {skill_path} 缺少 YAML frontmatter")
                return None

            frontmatter_text = frontmatter_match.group(1)
            skill_content = frontmatter_match.group(2).strip()

            # 解析 YAML
            try:
                frontmatter = yaml.safe_load(frontmatter_text)
            except yaml.YAMLError as e:
                print(f"❌ 解析 YAML frontmatter 失败: {e}")
                return None

            # 必需字段
            if "name" not in frontmatter or "description" not in frontmatter:
                print(f"⚠️  {skill_path} 缺少必需字段 (name 或 description)")
                return None

            # 创建 Skill 对象
            skill = Skill(
                name=frontmatter["name"],
                description=frontmatter["description"],
                content=skill_content,
                license=frontmatter.get("license"),
                allowed_tools=frontmatter.get("allowed-tools"),
                metadata=frontmatter.get("metadata"),
                skill_path=skill_path,
            )

            return skill

        except Exception as e:
            print(f"❌ 加载 skill 失败 ({skill_path}): {e}")
            return None

    def discover_skills(self) -> List[Skill]:
        """
        发现并加载 skills 目录中的所有 skills

        Returns:
            Skill 列表
        """
        skills = []

        if not self.skills_dir.exists():
            print(f"⚠️  Skills 目录不存在: {self.skills_dir}")
            return skills

        # 遍历所有子目录查找 SKILL.md
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                skill = self.load_skill(skill_file)
                if skill:
                    skills.append(skill)
                    self.loaded_skills[skill.name] = skill

        return skills

    def get_skill(self, name: str) -> Optional[Skill]:
        """
        获取已加载的 skill

        Args:
            name: skill 名称

        Returns:
            Skill 对象，如果不存在则返回 None
        """
        return self.loaded_skills.get(name)

    def list_skills(self) -> List[str]:
        """
        列出所有已加载的 skill 名称

        Returns:
            skill 名称列表
        """
        return list(self.loaded_skills.keys())

    def get_skills_prompt(self, skill_names: Optional[List[str]] = None) -> str:
        """
        生成包含指定 skills 的 prompt

        Args:
            skill_names: 要包含的 skill 名称列表，None 表示包含所有 skills

        Returns:
            组合的 prompt 字符串
        """
        if skill_names is None:
            skills = list(self.loaded_skills.values())
        else:
            skills = [
                self.loaded_skills[name]
                for name in skill_names
                if name in self.loaded_skills
            ]

        if not skills:
            return ""

        prompt_parts = ["# Available Skills\n"]
        for skill in skills:
            prompt_parts.append(skill.to_prompt())

        return "\n".join(prompt_parts)


# 示例用法
def load_example_skills() -> SkillLoader:
    """加载示例 skills（用于测试）"""
    loader = SkillLoader("./skills/example-skills")
    skills = loader.discover_skills()
    print(f"✅ 发现 {len(skills)} 个 skills:")
    for skill in skills:
        print(f"  - {skill.name}: {skill.description}")
    return loader


if __name__ == "__main__":
    # 测试
    loader = load_example_skills()
