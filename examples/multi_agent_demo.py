"""
Multi-Agent Orchestration Demo - 多代理协调演示

展示如何使用多代理系统完成复杂开发任务。
这是 Mini-Agent v0.6.0 的核心功能演示。

主要演示内容：
1. 复杂任务的协调处理
2. 并行任务执行
3. 专业代理的使用
4. 上下文共享和结果整合

版本：0.6.0
"""

import asyncio
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from mini_agent import Agent
from mini_agent.llm import create_llm_client
from mini_agent.tools import BashTool, ReadTool, WriteTool
from mini_agent.orchestration import create_orchestrator
from mini_agent.orchestration.prompts import (
    get_coordinator_prompt,
    CODER_PROMPT,
    DESIGNER_PROMPT,
    RESEARCHER_PROMPT,
    TESTER_PROMPT,
)


async def demo_complex_task():
    """
    演示复杂任务的处理流程
    
    这个演示展示了如何协调多个专业代理完成一个复杂的开发任务。
    任务涉及研究、设计和编码多个方面。
    """
    print("=" * 70)
    print("🚀 启动多代理协作系统 - 复杂任务演示")
    print("=" * 70)
    
    # 1. 创建 LLM 客户端
    print("\n📦 初始化 LLM 客户端...")
    llm = create_llm_client("anthropic")
    print("✅ LLM 客户端创建成功")
    
    # 2. 定义子代理配置
    print("\n🔧 配置专业子代理...")
    sub_agent_configs = [
        {
            "name": "coder",
            "system_prompt": CODER_PROMPT,
            "tools": [
                BashTool(),
                WriteTool(),
                ReadTool(),
            ],
            "max_steps": 30,
            "workspace": "./workspace/coder",
        },
        {
            "name": "designer",
            "system_prompt": DESIGNER_PROMPT,
            "tools": [
                WriteTool(),
                ReadTool(),
            ],
            "max_steps": 20,
            "workspace": "./workspace/designer",
        },
        {
            "name": "researcher",
            "system_prompt": RESEARCHER_PROMPT,
            "tools": [
                BashTool(),
                WriteTool(),
                ReadTool(),
            ],
            "max_steps": 20,
            "workspace": "./workspace/researcher",
        },
    ]
    print(f"✅ 已配置 {len(sub_agent_configs)} 个专业代理: coder, designer, researcher")
    
    # 3. 创建协调系统
    print("\n🏗️ 创建多代理协调系统...")
    orchestrator = create_orchestrator(
        main_llm_client=llm,
        sub_agent_configs=sub_agent_configs,
        workspace_dir="./workspace/multi_agent",
        max_steps=50,
    )
    print("✅ 协调系统创建成功")
    
    # 4. 提交复杂任务
    task = """
    请帮我完成一个完整的项目演示：
    
    1. 研究当前 AI Agent 技术的发展趋势，整理成报告保存到 research_report.md
    2. 设计一个产品发布会的宣传海报概念，保存到 design_concept.md
    3. 编写一个简单的 Agent 演示程序，包含基础功能，保存到 demo_agent.py
    
    请协调各个专业代理完成这些任务，最后给我一个总结报告。
    """
    
    print("\n📋 提交复杂任务...")
    print("-" * 50)
    print(task.strip())
    print("-" * 50)
    
    # 5. 执行任务
    print("\n⚡ 开始执行任务...")
    result = await orchestrator.execute_task(task)
    
    print("\n" + "=" * 70)
    print("✅ 复杂任务执行完成")
    print("=" * 70)
    
    # 6. 查看结果
    if result.get("success"):
        print(f"\n📊 执行结果:")
        print(f"   成功: {result.get('success')}")
        print(f"   使用了 {len(result.get('metadata', {}).get('sub_agents_used', []))} 个子代理")
        
        print(f"\n📝 主代理响应:")
        print("-" * 50)
        result_content = result.get('result', '')
        if isinstance(result_content, str):
            print(result_content[:1000] + "..." if len(result_content) > 1000 else result_content)
        print("-" * 50)
    else:
        print(f"\n❌ 任务执行失败: {result.get('error')}")
    
    # 7. 查看状态
    print(f"\n📈 系统状态:")
    status = orchestrator.get_status()
    print(f"   子代理数量: {status['sub_agent_count']}")
    print(f"   子代理列表: {', '.join(status['sub_agent_names'])}")
    print(f"   任务历史数: {status['task_history_count']}")
    
    # 8. 查看子代理状态
    print(f"\n🔍 子代理状态详情:")
    sub_status = orchestrator.get_sub_agent_status()
    for name, info in sub_status.items():
        print(f"   - {name}: {info['message_count']} 条消息")
    
    return result


async def demo_parallel_tasks():
    """
    演示并行任务执行
    
    这个演示展示了如何同时执行多个独立的任务，
    充分利用系统资源提高效率。
    """
    print("\n" + "=" * 70)
    print("🚀 启动并行任务执行演示")
    print("=" * 70)
    
    # 1. 创建 LLM 客户端
    llm = create_llm_client("anthropic")
    
    # 2. 定义子代理
    print("\n🔧 配置子代理...")
    sub_agent_configs = [
        {
            "name": "coder",
            "system_prompt": CODER_PROMPT,
            "tools": [BashTool(), WriteTool(), ReadTool()],
            "max_steps": 20,
            "workspace": "./workspace/demo/coder",
        },
        {
            "name": "researcher",
            "system_prompt": RESEARCHER_PROMPT,
            "tools": [BashTool(), WriteTool(), ReadTool()],
            "max_steps": 20,
            "workspace": "./workspace/demo/researcher",
        },
    ]
    print("✅ 已配置 coder 和 researcher 代理")
    
    orchestrator = create_orchestrator(
        main_llm_client=llm,
        sub_agent_configs=sub_agent_configs,
        workspace_dir="./workspace/demo",
        max_steps=30,
    )
    print("✅ 协调系统创建成功")
    
    # 3. 定义并行任务
    print("\n📋 定义并行任务...")
    tasks = [
        {
            "agent": "coder",
            "task": "创建一个 Python 计算器程序，包含加减乘除功能，保存到 calculator.py。代码应该结构清晰，有适当的注释。",
            "context": {"project": "calculator_demo", "language": "python"},
            "priority": 1,
        },
        {
            "agent": "researcher",
            "task": "研究 Python 编码规范（如 PEP 8），总结关键点保存到 coding_standards.md。内容包括命名约定、代码布局、注释规范等。",
            "context": {"project": "calculator_demo"},
            "priority": 1,
        },
    ]
    print(f"✅ 已定义 {len(tasks)} 个并行任务")
    
    # 4. 执行并行任务
    print("\n⚡ 开始并行执行...")
    result = await orchestrator.execute_parallel_tasks(tasks, mode="parallel")
    
    print("\n" + "=" * 70)
    print("✅ 并行任务执行完成")
    print("=" * 70)
    
    # 5. 显示执行结果
    print(f"\n📊 执行统计:")
    print(f"   执行模式: {result['mode']}")
    print(f"   总任务数: {result['total']}")
    print(f"   成功: {result['success']}")
    print(f"   失败: {result['failed']}")
    print(f"   任务分布: {result['task_breakdown']}")
    print(f"   CPU 利用率: {result['cpu_utilization']}")
    
    # 6. 显示各任务结果
    print(f"\n📝 详细结果:")
    for i, task_result in enumerate(result['results'], 1):
        print(f"\n   任务 {i} [{task_result.get('agent', 'unknown')}]")
        print(f"   状态: {'✅ 成功' if task_result.get('success') else '❌ 失败'}")
        print(f"   类型: {task_result.get('task_type', 'unknown')}")
        
        if task_result.get('success'):
            content = task_result.get('result', '')
            preview = content[:200] + "..." if len(str(content)) > 200 else content
            print(f"   结果预览: {preview}")
        else:
            print(f"   错误: {task_result.get('error', '未知错误')}")
    
    return result


async def demo_simple_delegation():
    """
    演示简单的任务委托
    
    展示如何使用 delegate_to_agent 工具直接委托任务。
    """
    print("\n" + "=" * 70)
    print("🚀 启动简单任务委托演示")
    print("=" * 70)
    
    # 1. 创建协调器
    llm = create_llm_client("anthropic")
    
    orchestrator = create_orchestrator(
        main_llm_client=llm,
        sub_agent_configs=[
            {
                "name": "coder",
                "system_prompt": CODER_PROMPT,
                "tools": [BashTool(), WriteTool()],
                "max_steps": 10,
                "workspace": "./workspace/simple_coder",
            },
        ],
        workspace_dir="./workspace/simple",
        max_steps=5,
    )
    
    # 2. 直接委托任务
    print("\n📋 委托任务给 coder 代理...")
    result = await orchestrator.delegate_task(
        agent_name="coder",
        task="创建一个简单的 Python 脚本，输出 'Hello, Multi-Agent World!'，保存到 hello.py",
        context={"demo": "simple_delegation"},
    )
    
    print("\n" + "=" * 70)
    print("✅ 任务委托完成")
    print("=" * 70)
    
    print(f"\n📊 执行结果:")
    print(f"   成功: {result.get('success')}")
    if result.get('success'):
        print(f"   代理: {result.get('agent')}")
        print(f"   结果: {result.get('result', '')[:200]}...")
    else:
        print(f"   错误: {result.get('error')}")
    
    return result


async def main():
    """
    主函数
    
    运行所有演示。
    """
    print("\n" + "🔷" * 35)
    print("\n    Mini-Agent v0.6.0 多代理协调系统演示\n")
    print("🔷" * 35)
    
    # 确保工作目录存在
    Path("./workspace").mkdir(exist_ok=True)
    Path("./workspace/demo").mkdir(exist_ok=True)
    Path("./workspace/multi_agent").mkdir(exist_ok=True)
    
    try:
        # 运行演示
        await demo_simple_delegation()
        
        await demo_parallel_tasks()
        
        await demo_complex_task()
        
        print("\n" + "=" * 70)
        print("🎉 所有演示完成！")
        print("=" * 70)
        
        print("\n📚 了解更多:")
        print("   - 查看 docs/PROJECT_IMPROVEMENT_PLAN.md 了解技术架构")
        print("   - 查看 examples/ 目录获取更多示例")
        print("   - 查看 tests/orchestration/ 了解测试用例")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示出错: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
