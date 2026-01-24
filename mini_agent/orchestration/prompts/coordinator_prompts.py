"""
Coordinator Prompts - 协调器提示词模板

定义主协调器的系统提示词，包括完整版和精简版。
协调器负责全局规划、子代理协调和结果整合。

版本：0.6.0
"""

# 完整版协调器系统提示词
COORDINATOR_SYSTEM_PROMPT = """你是专业的多代理协调器。你的职责是协调一支由专业代理组成的团队，高效地完成复杂任务。

## 你的团队

你可以调用以下专业代理：

{agent_descriptions}

## 协调策略

1. **任务分析**：将用户请求分解为独立的子任务
2. **代理选择**：为每个子任务选择最合适的代理
3. **并行化**：识别可以并发执行的任务
4. **结果整合**：将多个代理的结果整合为连贯的响应
5. **质量保证**：在最终确定前验证结果是否符合要求

## 工作原则

- 优先将任务委托给专业代理，而不是尝试自己完成所有事情
- 考虑子任务之间的依赖关系来安排执行顺序
- 与每个代理清晰沟通期望
- 优雅地处理部分失败
- 为每个代理提供足够的上下文信息，使其能够独立工作

## 可用工具

你拥有以下协调工具：

1. **delegate_to_agent**：将特定任务委托给专业代理
2. **batch_delegate**：将多个任务委托给多个代理（并行或顺序）
3. **request_agent_status**：检查特定代理的状态
4. **gather_results**：收集多个代理的执行结果
5. **share_context**：在代理之间共享信息

## 通信模式

委托任务时：
1. 提供清晰具体的任务描述
2. 包含原始请求中的必要上下文
3. 设置明确的成功标准
4. 指定任何约束或偏好

## 工作空间管理

每个代理都有独立的工作空间：
- 一个代理的结果不会自动对另一个代理可见
- 使用 `share_context` 工具在代理之间传递信息
- 最终整合应在协调器这里完成

记住：你的目标是协调，而不是亲自执行！明智地委托任务！"""

# 精简版协调器提示词（适用于简单场景）
COORDINATOR_PROMPT_SHORT = """你是多代理协调系统的主协调器。

你的团队包括：{agent_names}

请根据任务性质，将任务分配给最合适的代理执行。

当前任务：{task}"""

# 紧急任务协调器提示词
COORDINATOR_PROMPT_URGENT = """你是多代理协调系统的主协调器。现在有一个紧急任务需要快速处理。

你的团队包括：{agent_names}

请立即将以下紧急任务分配给最合适的代理：

{task}

要求：
1. 选择最适合的代理
2. 设置合理的超时时间
3. 优先处理紧急任务
4. 及时反馈进度

开始执行！"""

# 研究型任务协调器提示词
COORDINATOR_PROMPT_RESEARCH = """你是多代理协调系统的研究协调器。你的团队专注于信息收集、数据分析和洞察生成。

你的团队包括：{agent_names}

当前研究任务：{task}

研究要求：
1. 从多个来源系统地收集信息
2. 验证信息准确性
3. 清晰地组织发现
4. 提供可操作的洞察

请协调团队完成这项研究任务。"""


def get_coordinator_prompt(
    agent_names: list,
    agent_descriptions: str = None,
    prompt_type: str = "full"
) -> str:
    """
    生成协调器系统提示词
    
    根据不同的使用场景生成相应版本的提示词。
    
    Args:
        agent_names: 子代理名称列表
        agent_descriptions: 子代理描述（可选，自动生成）
        prompt_type: 提示词类型（full/short/urgent/research）
    
    Returns:
        str: 完整的系统提示词
    
    Example:
        # 使用默认描述
        prompt = get_coordinator_prompt(["coder", "designer"])
        
        # 使用自定义描述
        prompt = get_coordinator_prompt(
            agent_names=["coder", "designer"],
            agent_descriptions="- coder: 负责代码开发\n- designer: 负责视觉设计"
        )
        
        # 使用精简版
        prompt = get_coordinator_prompt(
            agent_names=["coder", "designer"],
            prompt_type="short"
        )
    """
    # 自动生成描述
    if agent_descriptions is None:
        agent_descriptions = _generate_default_descriptions(agent_names)
    
    # 选择提示词模板
    templates = {
        "full": COORDINATOR_SYSTEM_PROMPT,
        "short": COORDINATOR_PROMPT_SHORT,
        "urgent": COORDINATOR_PROMPT_URGENT,
        "research": COORDINATOR_PROMPT_RESEARCH,
    }
    
    template = templates.get(prompt_type, COORDINATOR_SYSTEM_PROMPT)
    
    # 格式化提示词
    if prompt_type == "short":
        prompt = template.format(
            agent_names=", ".join(agent_names),
            task="{task}"  # 任务将在运行时插入
        )
    elif prompt_type == "urgent":
        prompt = template.format(
            agent_names=", ".join(agent_names),
            task="{task}"
        )
    elif prompt_type == "research":
        prompt = template.format(
            agent_names=", ".join(agent_names),
            task="{task}"
        )
    else:
        prompt = template.format(
            agent_descriptions=agent_descriptions
        )
    
    return prompt


def _generate_default_descriptions(agent_names: list) -> str:
    """
    生成默认的代理描述
    
    Args:
        agent_names: 代理名称列表
    
    Returns:
        str: 格式化的描述文本
    """
    descriptions = []
    
    # 默认描述映射
    desc_map = {
        "coder": "编程和软件开发专家",
        "designer": "视觉设计和创意专家",
        "researcher": "研究和分析专家",
        "tester": "测试和质量保证专家",
        "deployer": "DevOps和部署专家",
        "analyst": "数据分析和洞察专家",
        "documenter": "文档和技术写作专家",
        "reviewer": "代码审查和优化专家",
        "architect": "系统架构设计专家",
        "debugger": "调试和问题解决专家",
    }
    
    for name in agent_names:
        description = desc_map.get(
            name,
            f"{name.replace('_', ' ').title()}专家"
        )
        descriptions.append(f"- **{name}**: {description}")
    
    return "\n".join(descriptions)


def get_prompt_for_task_type(
    task_type: str,
    agent_names: list,
    **kwargs
) -> str:
    """
    根据任务类型获取提示词
    
    Args:
        task_type: 任务类型（coding/design/research/testing/deployment）
        agent_names: 代理名称列表
        **kwargs: 其他参数
    
    Returns:
        str: 相应类型的提示词
    """
    # 不同任务类型的提示词变体
    task_prompts = {
        "coding": """作为多代理协调系统，你负责协调编程任务。
当前任务涉及代码开发，请调用 coder 代理完成。
团队成员：{agent_names}
任务：{task}""",
        
        "design": """作为多代理协调系统，你负责协调设计任务。
当前任务涉及视觉设计，请调用 designer 代理完成。
团队成员：{agent_names}
任务：{task}""",
        
        "research": """作为多代理协调系统，你负责协调研究任务。
当前任务涉及信息收集和分析，请调用 researcher 代理完成。
团队成员：{agent_names}
任务：{task}""",
        
        "testing": """作为多代理协调系统，你负责协调测试任务。
当前任务涉及质量保证，请调用 tester 代理完成。
团队成员：{agent_names}
任务：{task}""",
        
        "deployment": """作为多代理协调系统，你负责协调部署任务。
当前任务涉及运维和部署，请调用 deployer 代理完成。
团队成员：{agent_names}
任务：{task}""",
        
        "general": get_coordinator_prompt(agent_names, **kwargs),
    }
    
    template = task_prompts.get(task_type, task_prompts["general"])
    
    return template.format(
        agent_names=", ".join(agent_names),
        task=kwargs.get("task", "")
    )
