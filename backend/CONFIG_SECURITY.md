# Backend 配置文件

## 安全提醒 ⚠️

**请不要提交包含真实密钥的配置文件！**

本目录下的 `.env` 文件已被 `.gitignore` 忽略，但请确保：
- 不要在代码中硬编码密钥
- 不要提交 `.env` 文件
- 使用 `.env.example` 作为模板

## 配置说明

### LLM API 配置

支持多种 LLM 提供商：

#### 1. MiniMax
```env
LLM_API_KEY="your-minimax-api-key"
LLM_API_BASE="https://api.minimax.chat"
LLM_MODEL="MiniMax-Text-01"
LLM_PROVIDER="anthropic"
```

#### 2. 智谱 GLM
```env
LLM_API_KEY="your-glm-api-key"
LLM_API_BASE="https://open.bigmodel.cn/api/paas/v4/"
LLM_MODEL="glm-4"
LLM_PROVIDER="openai"
```

#### 3. OpenAI
```env
LLM_API_KEY="your-openai-api-key"
LLM_API_BASE="https://api.openai.com/v1"
LLM_MODEL="gpt-4"
LLM_PROVIDER="openai"
```

#### 4. Anthropic Claude
```env
LLM_API_KEY="your-anthropic-api-key"
LLM_API_BASE="https://api.anthropic.com"
LLM_MODEL="claude-3-5-sonnet-20241022"
LLM_PROVIDER="anthropic"
```

### LLM_PROVIDER 说明

- `anthropic`: 使用 Anthropic Messages API 格式
- `openai`: 使用 OpenAI Chat Completions API 格式

大多数兼容 OpenAI 的 API（如智谱 GLM、通义千问等）都应该使用 `openai`。

## 使用步骤

1. 复制示例文件
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填入你的配置
   ```bash
   vim .env
   ```

3. 确保不提交 `.env`
   ```bash
   git status  # 应该看不到 .env 文件
   ```

## 主配置文件位置

主配置文件 `mini_agent/config/config.yaml` 也包含 API 配置：
- 该文件已在 `.gitignore` 中
- 不会被 git 追踪
- 可以安全地存放密钥

## 配置优先级

Backend 使用环境变量（`.env`），与主配置文件（`config.yaml`）独立。
