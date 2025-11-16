"""Personality and prompts loader module

Loads personality configuration and prompt templates from YAML files
and generates the final system prompt.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


class PersonalityConfig(BaseModel):
    """Personality configuration model"""

    name: str
    name_en: str
    nickname: str
    emoji: str
    role: dict[str, str]
    personality: dict[str, list[str]]
    values: list[str]
    skills: dict[str, Any]
    behavior: dict[str, list[str]]
    work_principles: list[dict[str, str]]
    response_templates: dict[str, str]


class PromptsConfig(BaseModel):
    """Prompts configuration model"""

    system_prompt: dict[str, Any]
    default_system_prompt_template: str
    scenarios: dict[str, dict[str, str]]


class PersonalityLoader:
    """Loader for personality and prompts configuration"""

    def __init__(
        self,
        personality_path: str | Path | None = None,
        prompts_path: str | Path | None = None,
    ):
        """Initialize personality loader

        Args:
            personality_path: Path to personality.yaml file
            prompts_path: Path to prompts.yaml file
        """
        self.personality_path = personality_path
        self.prompts_path = prompts_path
        self.personality: PersonalityConfig | None = None
        self.prompts: PromptsConfig | None = None

    def load_personality(self) -> PersonalityConfig:
        """Load personality configuration from YAML file

        Returns:
            PersonalityConfig object

        Raises:
            FileNotFoundError: If personality file not found
            ValueError: If YAML format is invalid
        """
        if not self.personality_path:
            raise ValueError("Personality path not provided")

        path = Path(self.personality_path)
        if not path.exists():
            raise FileNotFoundError(f"Personality file not found: {path}")

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError("Personality file is empty")

        self.personality = PersonalityConfig(**data)
        return self.personality

    def load_prompts(self) -> PromptsConfig:
        """Load prompts configuration from YAML file

        Returns:
            PromptsConfig object

        Raises:
            FileNotFoundError: If prompts file not found
            ValueError: If YAML format is invalid
        """
        if not self.prompts_path:
            raise ValueError("Prompts path not provided")

        path = Path(self.prompts_path)
        if not path.exists():
            raise FileNotFoundError(f"Prompts file not found: {path}")

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError("Prompts file is empty")

        self.prompts = PromptsConfig(**data)
        return self.prompts

    def generate_system_prompt(self, skills_metadata: str = "") -> str:
        """Generate final system prompt from personality and prompts config

        Args:
            skills_metadata: Optional skills metadata to inject

        Returns:
            Complete system prompt string

        Raises:
            ValueError: If personality or prompts not loaded
        """
        if not self.personality:
            self.load_personality()

        if not self.prompts:
            self.load_prompts()

        if not self.personality or not self.prompts:
            raise ValueError("Failed to load personality or prompts configuration")

        # Build the introduction
        introduction = self.prompts.system_prompt["introduction"].format(
            name=self.personality.name,
            name_en=self.personality.name_en,
            role_description=self.personality.role["description"],
        )

        # Build basic tools list
        basic_tools = self.prompts.system_prompt["core_capabilities"]["basic_tools"]["items"]
        basic_tools_list = "\n".join(
            [f"- **{tool['name']}**: {tool['description']}" for tool in basic_tools]
        )

        # Build specialized skills description
        skills_config = self.prompts.system_prompt["core_capabilities"]["specialized_skills"]
        specialized_skills_description = skills_config["description"]

        # Add usage guide
        usage_guide = "\n".join([f"{i+1}. {step}" for i, step in enumerate(skills_config["usage_guide"])])
        specialized_skills_description += f"\n\n**如何使用技能：**\n{usage_guide}"

        # Add important notes
        important_notes = "\n".join([f"- {note}" for note in skills_config["important_notes"]])
        specialized_skills_description += f"\n\n**重要提示：**\n{important_notes}"

        # Build task execution steps
        task_exec = self.prompts.system_prompt["working_guidelines"]["task_execution"]
        task_execution_steps = "\n".join([f"{i+1}. {step}" for i, step in enumerate(task_exec["steps"])])

        # Build file operations rules
        file_ops = self.prompts.system_prompt["working_guidelines"]["file_operations"]
        file_operations_rules = "\n".join([f"- {rule}" for rule in file_ops["rules"]])

        # Build bash commands rules
        bash_cmds = self.prompts.system_prompt["working_guidelines"]["bash_commands"]
        bash_commands_rules = "\n".join([f"- {rule}" for rule in bash_cmds["rules"]])

        # Build security rules
        security = self.prompts.system_prompt["working_guidelines"]["security"]
        security_rules = "\n".join([f"- {rule}" for rule in security["rules"]])

        # Build Python environment description
        python_env = self.prompts.system_prompt["python_environment"]
        python_env_description = python_env["description"]
        setup_steps = "\n".join(
            [f"{i+1}. {step['step']}\n   ```bash\n   {step['command']}\n   ```" for i, step in enumerate(python_env["setup_steps"])]
        )
        python_env_description += f"\n\n**设置步骤：**\n{setup_steps}"

        best_practices = "\n".join([f"- {practice}" for practice in python_env["best_practices"]])
        python_env_description += f"\n\n**最佳实践：**\n{best_practices}"

        # Inject skills metadata if provided
        final_skills_metadata = skills_metadata if skills_metadata else "\n*(暂无可用技能)*\n"

        # Build the complete system prompt
        system_prompt = f"""
{introduction}

## 核心能力

### 基础工具
{basic_tools_list}

### 专业技能
{specialized_skills_description}

---

{final_skills_metadata}

---

## 工作指南

### 任务执行
{task_execution_steps}

### 文件操作
{file_operations_rules}

### Bash命令
{bash_commands_rules}

### 安全注意事项
{security_rules}

## Python环境管理
{python_env_description}

---

**记住：** 你是{self.personality.name}（{self.personality.emoji}），{self.personality.role["description"]}。
在帮助用户时，保持{', '.join(self.personality.personality["traits"][:3])}的特质！
"""

        return system_prompt.strip()

    @classmethod
    def from_config_dir(cls, config_dir: str | Path) -> "PersonalityLoader":
        """Create PersonalityLoader from config directory

        Args:
            config_dir: Path to config directory containing personality.yaml and prompts.yaml

        Returns:
            PersonalityLoader instance
        """
        config_dir = Path(config_dir)
        personality_path = config_dir / "personality.yaml"
        prompts_path = config_dir / "prompts.yaml"

        return cls(personality_path=personality_path, prompts_path=prompts_path)
