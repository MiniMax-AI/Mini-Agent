"""
Prompt Templates - 提示词模板模块

提供协调器和各类专业代理的系统提示词模板。
这些提示词经过优化，用于指导不同类型代理的行为。

主要导出：
- 协调器提示词：get_coordinator_prompt, COORDINATOR_SYSTEM_PROMPT
- 专业代理提示词：CODER_PROMPT, DESIGNER_PROMPT, RESEARCHER_PROMPT 等
- 工具函数：get_agent_prompt, create_agent_config

版本：0.6.0
"""

from .coordinator_prompts import (
    get_coordinator_prompt,
    COORDINATOR_SYSTEM_PROMPT,
    COORDINATOR_PROMPT_SHORT,
    COORDINATOR_PROMPT_URGENT,
    COORDINATOR_PROMPT_RESEARCH,
)

from .agent_prompts import (
    CODER_PROMPT,
    DESIGNER_PROMPT,
    RESEARCHER_PROMPT,
    TESTER_PROMPT,
    DEPLOYER_PROMPT,
    ANALYST_PROMPT,
    DOCUMENTER_PROMPT,
    REVIEWER_PROMPT,
    ARCHITECT_PROMPT,
    DEBUGGER_PROMPT,
    get_agent_prompt,
    create_agent_config,
)

__version__ = "0.6.0"

__all__ = [
    # 协调器提示词
    "get_coordinator_prompt",
    "COORDINATOR_SYSTEM_PROMPT",
    "COORDINATOR_PROMPT_SHORT",
    "COORDINATOR_PROMPT_URGENT",
    "COORDINATOR_PROMPT_RESEARCH",
    
    # 专业代理提示词
    "CODER_PROMPT",
    "DESIGNER_PROMPT",
    "RESEARCHER_PROMPT",
    "TESTER_PROMPT",
    "DEPLOYER_PROMPT",
    "ANALYST_PROMPT",
    "DOCUMENTER_PROMPT",
    "REVIEWER_PROMPT",
    "ARCHITECT_PROMPT",
    "DEBUGGER_PROMPT",
    
    # 工具函数
    "get_agent_prompt",
    "create_agent_config",
]
