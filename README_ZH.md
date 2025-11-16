# 叶灵华 (Ye Linghua) 🌸

> 一个热爱编程的AI少女助手

叶灵华是一个功能强大的AI助手，专注于帮助开发者解决编程问题。她热情开朗、技术精湛，拥有完整的工具链和可定制的人设系统。

## ✨ 核心特性

### 🎭 人设系统
- **YAML配置**: 完全可定制的人设配置文件
- **灵活的提示词模板**: 支持多场景、多模板的提示词系统
- **Web配置界面**: 友好的Web界面用于编辑人设和提示词
- **实时预览**: 即时查看配置效果

### 🤖 多模型支持
- **Anthropic Claude**: 支持Claude系列模型
- **OpenAI兼容**: 支持OpenAI协议的所有模型
- **多模态输入**: 支持文本和图像的混合输入
- **思考内容分离**: 支持Reasoning/Thinking内容的独立处理

### 🛠️ 丰富的工具生态
- **文件操作**: 读取、写入、编辑文件
- **Bash执行**: 运行系统命令和脚本
- **MCP工具**: 支持Model Context Protocol工具集成
- **技能系统**: 渐进式加载的专业技能库
- **会话记忆**: 跨会话的记忆和笔记功能

## 📦 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/Ye_Linghua.git
cd Ye_Linghua

# 安装依赖
pip install -e .

# 或使用uv（推荐）
uv pip install -e .
```

## 🚀 快速开始

### 1. 配置API密钥

创建配置文件目录：
```bash
mkdir -p ~/.ye-linghua/config
```

复制示例配置：
```bash
cp ye_linghua/config/config-example.yaml ~/.ye-linghua/config/config.yaml
cp ye_linghua/config/personality.yaml ~/.ye-linghua/config/
cp ye_linghua/config/prompts.yaml ~/.ye-linghua/config/
```

编辑配置文件，添加你的API密钥：
```bash
nano ~/.ye-linghua/config/config.yaml
```

### 2. 启动叶灵华

```bash
# 启动CLI交互模式
ye-linghua

# 指定工作目录
ye-linghua --workspace /path/to/your/project
```

### 3. 使用Web配置界面

```bash
# 启动Web配置界面
ye-linghua-config
```

然后在浏览器中打开 http://localhost:8000

## 🎨 人设配置

### personality.yaml 结构

```yaml
name: "叶灵华"
name_en: "Ye Linghua"
emoji: "🌸"

role:
  title: "AI编程助手"
  description: "一个热爱编程、充满活力的AI少女"

personality:
  traits:
    - "热情开朗"
    - "好奇心强"
    - "追求完美"

  interests:
    - "编程与算法"
    - "开源项目"
    - "技术博客"

skills:
  programming_languages:
    - Python
    - JavaScript
    - TypeScript

behavior:
  greeting:
    - "你好！我是叶灵华，很高兴能帮助你解决编程问题！"
```

### prompts.yaml 结构

```yaml
system_prompt:
  introduction: |
    你是{name}（{name_en}），{role_description}。
    你充满热情，热爱编程，善于用清晰易懂的方式帮助用户解决技术问题。

  core_capabilities:
    basic_tools:
      items:
        - name: "文件操作"
          description: "读取、写入、编辑文件"
        - name: "Bash执行"
          description: "运行命令、管理git"

  working_guidelines:
    task_execution:
      steps:
        - "**分析**请求，识别是否有技能可以帮助"
        - "**分解**复杂任务为清晰、可执行的步骤"
        - "**系统化执行**工具并检查结果"
```

## 🔧 配置选项

### config.yaml 主要配置

```yaml
# LLM配置
api_key: "YOUR_API_KEY"
api_base: "https://api.minimax.io"
model: "MiniMax-M2"
provider: "anthropic"  # "anthropic" 或 "openai"

# Agent配置
agent:
  max_steps: 100
  workspace_dir: "./workspace"

  # 人设系统
  use_personality: true
  personality_path: "personality.yaml"
  prompts_path: "prompts.yaml"

# 工具配置
tools:
  enable_file_tools: true
  enable_bash: true
  enable_skills: true
  enable_mcp: true
```

## 💻 使用示例

### Python API

```python
from ye_linghua import LLMClient, YeLinghua
from ye_linghua.config import Config
from ye_linghua.schema import LLMProvider

# 加载配置
config = Config.from_yaml("~/.ye-linghua/config/config.yaml")

# 创建LLM客户端
llm_client = LLMClient(
    api_key=config.llm.api_key,
    provider=LLMProvider.OPENAI,
    model="gpt-4",
)

# 创建Agent（使用YeLinghua别名）
agent = YeLinghua(
    llm_client=llm_client,
    system_prompt="你是叶灵华，热爱编程的AI助手",
    tools=tools,
)

# 添加用户消息
agent.add_user_message("帮我写一个快速排序算法")

# 运行
await agent.run()
```

### 多模态输入示例

```python
# 发送包含图像的消息
agent.add_user_message([
    {"type": "text", "text": "这张图片中的代码有什么问题？"},
    {
        "type": "image_url",
        "image_url": {"url": "https://example.com/code-screenshot.png"}
    }
])

await agent.run()
```

## 🌐 Web配置界面功能

### 人设编辑
- 实时编辑personality.yaml
- YAML语法高亮和验证
- 保存到用户配置目录

### 提示词编辑
- 编辑prompts.yaml模板
- 支持变量占位符
- 实时保存

### 预览生成
- 生成完整系统提示词预览
- 查看实际效果
- 调试和优化提示词

## 🎯 命令行工具

```bash
# 启动交互式CLI
ye-linghua [--workspace DIR]

# 启动Web配置界面
ye-linghua-config

# 查看版本
ye-linghua --version

# 查看帮助
ye-linghua --help
```

## 🔄 从Mini-Agent迁移

如果你之前使用的是Mini-Agent，迁移非常简单：

1. 安装新版本
2. 更新导入语句：
   ```python
   # 旧的
   from mini_agent import Agent, LLMClient

   # 新的
   from ye_linghua import Agent, LLMClient, YeLinghua
   ```
3. 配置文件会自动迁移（保持向后兼容）
4. 可选：启用新的人设系统（`use_personality: true`）

## 📚 项目结构

```
Ye_Linghua/
├── ye_linghua/
│   ├── __init__.py              # 包导出（Agent, YeLinghua别名）
│   ├── agent.py                 # 核心Agent类
│   ├── cli.py                   # CLI交互界面
│   ├── config.py                # 配置管理
│   ├── personality_loader.py    # 人设加载器
│   ├── web_config.py            # Web配置界面
│   │
│   ├── llm/                     # LLM客户端
│   │   ├── base.py
│   │   ├── anthropic_client.py
│   │   ├── openai_client.py     # 支持多模态
│   │   └── llm_wrapper.py
│   │
│   ├── config/                  # 配置文件
│   │   ├── config-example.yaml
│   │   ├── personality.yaml     # 人设配置
│   │   ├── prompts.yaml         # 提示词配置
│   │   ├── system_prompt.md     # 传统提示词（向后兼容）
│   │   └── mcp.json
│   │
│   ├── tools/                   # 工具实现
│   └── skills/                  # 技能库
│
├── examples/                    # 示例代码
├── tests/                       # 测试
├── pyproject.toml
└── README_ZH.md
```

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 基于 [Mini-Agent](https://github.com/MiniMax-AI/Mini-Agent) 项目重构
- 感谢 MiniMax 提供强大的AI模型支持
- 感谢所有贡献者

## 📞 联系方式

- Issues: [GitHub Issues](https://github.com/yourusername/Ye_Linghua/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/Ye_Linghua/discussions)

---

**Made with 💖 by the Ye Linghua Team**
