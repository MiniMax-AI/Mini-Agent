# Agent 生产环境部署指南

> 从 Demo 到生产的完整进阶指南

## 目录

- [1. Demo vs 生产环境概览](#1-demo-vs-生产环境概览)
- [2. 核心升级方向](#2-核心升级方向)
- [3. 架构升级方案](#3-架构升级方案)
- [4. 实施路线图](#4-实施路线图)

---

## 1. Demo vs 生产环境概览

本项目是**教学级 Demo**，展示了 Agent 的核心概念和执行链路。要达到生产级别，还需要处理大量复杂问题。

### 我们实现的（Demo 级别）

| 功能                  | Demo 实现                   | 复杂度 |
| --------------------- | --------------------------- | ------ |
| **Session Note Tool** | ✅ 简单的 JSON 文件存储      | ⭐ 入门 |
| **工具调用**          | ✅ 基础 Read/Write/Edit/Bash | ⭐ 入门 |
| **错误处理**          | ✅ 基础异常捕获              | ⭐ 入门 |
| **日志**              | ✅ 简单 print 输出           | ⭐ 入门 |

### 时间投入估算

| 阶段         | Demo 实现 | 生产实现  | 复杂度倍数 |
| ------------ | --------- | --------- | ---------- |
| **基础功能** | 1周       | 1-2月     | 5-10x      |
| **进阶特性** | -         | 2-4月     | -          |
| **生产优化** | -         | 2-3月     | -          |
| **总计**     | **1周**   | **6-9月** | **30-40x** |

---

## 2. 核心升级方向

### 2.1 高级笔记管理 ⭐⭐⭐⭐

**Demo 方案（当前实现）**:
- 简单的 JSON 文件存储
- 按类别 (category) 直接检索
- 无过期机制

**生产方案**:

#### 向量数据库存储
```python
from pymilvus import connections, Collection

# 连接向量数据库
connections.connect("default", host="localhost", port="19530")
collection = Collection("agent_notes")

# 存储笔记（带 embedding）
embedding = get_embedding(note_content)  # 使用 OpenAI/MiniMax embedding
collection.insert([{
    "content": note_content,
    "category": "user_preference",
    "embedding": embedding,
    "importance": 0.8,
    "timestamp": datetime.now()
}])
```

#### 语义搜索
```python
# 通过语义相似度检索，而非简单的分类过滤
query_embedding = get_embedding("用户喜欢什么编程风格?")
results = collection.search(
    data=[query_embedding],
    anns_field="embedding",
    param={"metric_type": "L2", "params": {"nprobe": 10}},
    limit=5
)
```

#### 智能去重与重要性评分
```python
class NoteManager:
    def add_note(self, content: str, category: str):
        # 1. 检测相似笔记
        similar_notes = self.find_similar(content, threshold=0.9)
        
        if similar_notes:
            # 2. 合并笔记，更新重要性
            self.merge_notes(similar_notes[0], content)
        else:
            # 3. 新笔记，计算初始重要性
            importance = self.calculate_importance(content, category)
            self.store_note(content, category, importance)
    
    def calculate_importance(self, content: str, category: str) -> float:
        """
        重要性评分算法：
        - 用户偏好: 0.9
        - 项目配置: 0.8
        - 临时信息: 0.3
        """
        weights = {
            "user_preference": 0.9,
            "project_info": 0.8,
            "temp_info": 0.3
        }
        return weights.get(category, 0.5)
```

#### 时间衰减与综合评分
```python
def retrieve_notes(self, query: str, top_k: int = 5):
    """
    综合评分算法：
    - 语义相似度: 70%
    - 重要性: 20%
    - 时间因素: 10%
    """
    query_embedding = get_embedding(query)
    
    # 1. 语义搜索
    candidates = self.vector_search(query_embedding, top_k=20)
    
    # 2. 综合评分
    for note in candidates:
        # 时间衰减（越新权重越高）
        time_weight = self.time_decay(note.timestamp)
        
        # 综合分数
        note.final_score = (
            note.similarity * 0.7 +
            note.importance * 0.2 +
            time_weight * 0.1
        )
    
    # 3. 返回 top-k
    return sorted(candidates, key=lambda x: x.final_score, reverse=True)[:top_k]
```

---

### 2.2 精确的上下文截断处理 ⭐⭐⭐⭐

**Demo 方案（当前实现）**:
- 无消息截断逻辑
- 依赖 LLM 的 context window 限制
- 超出限制时直接报错

**生产方案**:

#### 精确 Token 计数
```python
import tiktoken

class ContextManager:
    def __init__(self, model: str, max_tokens: int):
        self.model = model
        self.max_tokens = max_tokens
        self.encoder = tiktoken.encoding_for_model(model)
    
    def count_tokens(self, messages: List[Dict]) -> int:
        """精确计算消息的 token 数"""
        total = 0
        for msg in messages:
            # 消息格式的固定 token（role, content 等）
            total += 4
            
            # 内容 token
            if isinstance(msg["content"], str):
                total += len(self.encoder.encode(msg["content"]))
            elif isinstance(msg["content"], list):
                # 处理多模态消息
                for item in msg["content"]:
                    if item["type"] == "text":
                        total += len(self.encoder.encode(item["text"]))
        
        return total
```

#### 滑动窗口策略
```python
def truncate_messages(self, messages: List[Dict]) -> List[Dict]:
    """
    智能截断策略：
    1. System prompt 永远保留
    2. 最近 N 条消息优先保留
    3. 重要消息打标保留
    4. 其他消息按重要性截断
    """
    # Token 预算分配
    budget = {
        "system": int(self.max_tokens * 0.1),    # 10%
        "recent": int(self.max_tokens * 0.4),    # 40%
        "context": int(self.max_tokens * 0.5)    # 50%
    }
    
    result = []
    
    # 1. 保留 system prompt
    system_msg = messages[0]
    result.append(system_msg)
    current_tokens = self.count_tokens([system_msg])
    
    # 2. 保留最近消息
    recent_messages = messages[-10:]  # 最近10条
    recent_tokens = self.count_tokens(recent_messages)
    
    if current_tokens + recent_tokens <= budget["system"] + budget["recent"]:
        result.extend(recent_messages)
        current_tokens += recent_tokens
    else:
        # 需要截断 recent messages
        result.extend(self._truncate_by_priority(
            recent_messages, 
            budget["recent"]
        ))
    
    # 3. 填充中间的重要消息
    remaining_budget = self.max_tokens - current_tokens
    middle_messages = messages[1:-10]
    
    # 按重要性排序并选择
    important_msgs = self._select_important(middle_messages, remaining_budget)
    result[1:1] = important_msgs  # 插入到 system 后面
    
    return result
```

#### 工具调用结果压缩
```python
async def compress_tool_result(self, result: str, max_tokens: int = 500) -> str:
    """
    长结果自动摘要（使用小模型）
    """
    if len(self.encoder.encode(result)) <= max_tokens:
        return result
    
    # 使用 Claude Haiku 或 GPT-3.5 进行摘要
    summary = await self.llm.generate(
        messages=[{
            "role": "user",
            "content": f"请将以下内容压缩到 {max_tokens} token 以内，保留关键信息：\n\n{result}"
        }],
        model="claude-3-haiku-20240307",
        max_tokens=max_tokens
    )
    
    return summary.content
```

---

### 2.3 模型 Fallback 机制 ⭐⭐⭐⭐⭐

**Demo 方案（当前实现）**:
- 固定使用单一模型 (MiniMax-M2)
- 失败时直接报错

**生产方案**:

#### 多模型池管理
```python
class ModelPool:
    def __init__(self):
        # 三层模型池
        self.tiers = {
            "primary": [
                {"name": "MiniMax-M2", "cost": 0.01, "speed": "fast"},
                {"name": "claude-3-5-sonnet-20241022", "cost": 0.015, "speed": "medium"}
            ],
            "backup": [
                {"name": "gpt-4o", "cost": 0.03, "speed": "medium"},
                {"name": "claude-3-opus-20240229", "cost": 0.075, "speed": "slow"}
            ],
            "fallback": [
                {"name": "claude-3-haiku-20240307", "cost": 0.0025, "speed": "fast"},
                {"name": "gpt-3.5-turbo", "cost": 0.002, "speed": "fast"}
            ]
        }
        
        # 记录每个模型的失败次数
        self.failure_count = defaultdict(int)
        self.max_failures = 3
```

#### 智能模型选择
```python
def select_model(self, task_complexity: str, budget: float) -> str:
    """
    根据任务复杂度和预算选择模型
    """
    # 任务复杂度评估
    if task_complexity == "simple":
        # 简单任务：格式转换、数据提取
        tier = "fallback"
    elif task_complexity == "medium":
        # 普通任务：一般对话、简单推理
        tier = "primary"
    else:
        # 复杂任务：深度推理、规划
        tier = "backup"
    
    # 在该层级选择可用且在预算内的模型
    available = [
        m for m in self.tiers[tier]
        if self.failure_count[m["name"]] < self.max_failures
        and m["cost"] <= budget
    ]
    
    if not available:
        # 降级到下一层
        return self._downgrade_tier(tier, budget)
    
    # 选择该层最便宜的模型
    return min(available, key=lambda x: x["cost"])["name"]
```

#### 自动故障切换
```python
async def call_with_fallback(self, messages: List[Dict], max_retries: int = 3):
    """
    自动故障切换
    """
    tiers = ["primary", "backup", "fallback"]
    
    for tier in tiers:
        models = self.tiers[tier]
        
        for model in models:
            # 跳过失败次数过多的模型
            if self.failure_count[model["name"]] >= self.max_failures:
                logger.warning(f"跳过模型 {model['name']}（失败次数过多）")
                continue
            
            try:
                response = await self.llm.generate(
                    messages=messages,
                    model=model["name"],
                    max_tokens=2000
                )
                
                # 成功，重置失败计数
                self.failure_count[model["name"]] = 0
                return response
                
            except Exception as e:
                # 记录失败
                self.failure_count[model["name"]] += 1
                logger.error(f"模型 {model['name']} 调用失败: {e}")
                
                # 继续尝试下一个模型
                continue
    
    # 所有模型都失败
    raise RuntimeError("所有模型都不可用")
```

#### 健康检测
```python
async def health_check(self):
    """
    定期检测各模型可用性
    """
    for tier, models in self.tiers.items():
        for model in models:
            try:
                start_time = time.time()
                
                # 发送简单测试请求
                await self.llm.generate(
                    messages=[{"role": "user", "content": "hello"}],
                    model=model["name"],
                    max_tokens=10
                )
                
                latency = time.time() - start_time
                
                # 记录健康状态
                self.health_status[model["name"]] = {
                    "status": "healthy",
                    "latency": latency,
                    "last_check": datetime.now()
                }
                
                # 如果恢复，重置失败计数
                if self.failure_count[model["name"]] > 0:
                    logger.info(f"模型 {model['name']} 已恢复")
                    self.failure_count[model["name"]] = 0
                    
            except Exception as e:
                self.health_status[model["name"]] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.now()
                }
```

---

### 2.4 模型幻觉检测与修正 ⭐⭐⭐⭐⭐

**Demo 方案（当前实现）**:
- 直接信任模型输出
- 无验证机制

**生产方案（Reflection 反思系统）**:

#### 工具调用前验证
```python
class ToolCallValidator:
    DANGEROUS_COMMANDS = [
        r"rm\s+-rf\s+/",
        r"dd\s+if=",
        r"mkfs\.",
        r":(){ :|:& };:",  # Fork bomb
    ]
    
    def validate_tool_call(self, tool_name: str, arguments: Dict) -> Tuple[bool, str]:
        """
        验证工具调用的安全性
        """
        # 1. 参数类型检查
        if not self._check_types(tool_name, arguments):
            return False, "参数类型不正确"
        
        # 2. 路径安全性验证
        if tool_name in ["read_file", "write_file", "edit_file"]:
            if not self._check_path_safety(arguments.get("file_path")):
                return False, "路径不安全（检测到目录遍历尝试）"
        
        # 3. 命令危险性检测
        if tool_name == "bash":
            if self._is_dangerous_command(arguments.get("command")):
                return False, "检测到危险命令"
        
        # 4. 执行前预测
        prediction = await self._predict_outcome(tool_name, arguments)
        if not self._validate_prediction(prediction):
            return False, f"预测结果异常: {prediction}"
        
        return True, "验证通过"
    
    def _is_dangerous_command(self, command: str) -> bool:
        """检测危险命令"""
        for pattern in self.DANGEROUS_COMMANDS:
            if re.search(pattern, command):
                return True
        return False
    
    async def _predict_outcome(self, tool_name: str, arguments: Dict) -> str:
        """
        询问模型："这个操作会做什么？"
        """
        response = await self.llm.generate(
            messages=[{
                "role": "user",
                "content": f"工具 {tool_name} 使用参数 {arguments} 会产生什么结果？请简要描述。"
            }],
            model="claude-3-haiku-20240307",
            max_tokens=200
        )
        return response.content
```

#### 执行后结果验证
```python
class ResultValidator:
    async def validate_result(
        self, 
        tool_name: str, 
        arguments: Dict, 
        result: ToolResult,
        expected: str = None
    ) -> bool:
        """
        验证工具执行结果
        """
        # 1. 对比实际结果与预期结果
        if expected:
            similarity = self._calculate_similarity(result.content, expected)
            if similarity < 0.7:
                logger.warning(f"结果与预期不符（相似度：{similarity}）")
                return False
        
        # 2. 异常检测
        if not self._is_result_reasonable(tool_name, result):
            logger.warning(f"结果异常：{result.content[:100]}")
            return False
        
        # 3. 副作用检查
        if tool_name in ["write_file", "bash"]:
            side_effects = await self._check_side_effects(arguments)
            if side_effects:
                logger.warning(f"检测到意外副作用：{side_effects}")
                return False
        
        return True
    
    async def _check_side_effects(self, arguments: Dict) -> List[str]:
        """
        检查是否产生了意外的文件修改
        """
        # 记录执行前的文件状态
        before = self._snapshot_workspace()
        
        # （工具已执行）
        
        # 记录执行后的文件状态
        after = self._snapshot_workspace()
        
        # 对比差异
        unexpected = []
        for file, checksum in after.items():
            if file not in before:
                unexpected.append(f"新增文件: {file}")
            elif before[file] != checksum:
                # 检查是否是预期的修改
                if not self._is_expected_modification(file, arguments):
                    unexpected.append(f"意外修改: {file}")
        
        return unexpected
```

#### 自我反思机制
```python
class ReflectionSystem:
    async def reflect_on_answer(self, question: str, answer: str) -> Tuple[bool, str]:
        """
        要求模型对自己的答案进行反思
        """
        # 1. 解释推理过程
        reasoning = await self.llm.generate(
            messages=[{
                "role": "user",
                "content": f"你刚才回答了：\n问题：{question}\n答案：{answer}\n\n请解释你的推理过程。"
            }],
            model="claude-3-5-sonnet-20241022",
            max_tokens=500
        )
        
        # 2. 询问确信度
        confidence = await self.llm.generate(
            messages=[{
                "role": "user",
                "content": f"对于上述答案，你的确信度是多少（0-100）？如果不确定，请说明原因。"
            }],
            model="claude-3-5-sonnet-20241022",
            max_tokens=200
        )
        
        # 3. 检测前后矛盾
        history_answers = self._get_history_answers(question)
        if history_answers:
            is_consistent = await self._check_consistency(answer, history_answers)
            if not is_consistent:
                return False, "答案与历史回答矛盾"
        
        return True, reasoning.content
```

#### 多模型交叉验证
```python
async def cross_validate(self, question: str, critical: bool = False) -> str:
    """
    重要决策使用多个模型验证
    """
    if not critical:
        # 非关键决策，使用单模型
        return await self.llm.generate_simple(question)
    
    # 关键决策，使用3个不同模型
    models = [
        "MiniMax-M2",
        "claude-3-5-sonnet-20241022",
        "gpt-4o"
    ]
    
    answers = []
    for model in models:
        answer = await self.llm.generate(
            messages=[{"role": "user", "content": question}],
            model=model,
            max_tokens=1000
        )
        answers.append(answer.content)
    
    # 对比结果
    if self._all_agree(answers):
        return answers[0]
    else:
        # 结果不一致，触发人工介入
        logger.warning(f"模型结果不一致：\n{answers}")
        return await self._request_human_review(question, answers)
```

#### 自动纠错流程
```python
async def auto_correct(
    self, 
    tool_name: str, 
    arguments: Dict, 
    error_msg: str,
    max_retries: int = 3
) -> ToolResult:
    """
    检测到问题时自动纠错
    """
    for i in range(max_retries):
        # 1. 提供错误提示
        correction_prompt = f"""
        你刚才调用工具 {tool_name} 时出错了：
        
        参数：{arguments}
        错误：{error_msg}
        
        请重新思考并生成正确的工具调用。注意以下约束：
        - 确保路径存在且安全
        - 确保命令不包含危险操作
        - 确保参数类型正确
        """
        
        # 2. 要求模型重新生成
        response = await self.llm.generate(
            messages=[{"role": "user", "content": correction_prompt}],
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000
        )
        
        # 3. 提取新的工具调用
        new_tool_call = self._extract_tool_call(response.content)
        
        # 4. 验证新的调用
        valid, msg = await self.validator.validate_tool_call(
            new_tool_call.name,
            new_tool_call.arguments
        )
        
        if valid:
            # 5. 执行
            result = await self.execute_tool(new_tool_call.name, new_tool_call.arguments)
            if result.success:
                logger.info(f"纠错成功（第 {i+1} 次尝试）")
                return result
        
        error_msg = msg
    
    # 最多重试 3 次失败，人工介入
    logger.error(f"自动纠错失败，需要人工介入")
    raise RuntimeError("自动纠错失败")
```

**实际案例：防止误删除**
```python
# 用户输入
user_input = "帮我把所有 .txt 文件移到 backup 目录"

# ❌ 无验证系统
tool_call = {
    "name": "bash",
    "arguments": {"command": "rm *.txt"}  # 直接删除！
}

# ✅ 有验证系统
# 1. 预测检测
prediction = await validator.predict_outcome("bash", {"command": "rm *.txt"})
# prediction = "会删除所有 txt 文件"

# 2. 验证失败
is_valid = validator.validate_prediction(user_input, prediction)
# is_valid = False （任务是"移动"，不是"删除"）

# 3. 要求重新生成
corrected_call = await auto_correct(
    tool_name="bash",
    arguments={"command": "rm *.txt"},
    error_msg="任务要求移动文件，而非删除"
)
# corrected_call = {"command": "mkdir -p backup && mv *.txt backup/"}
```

---

### 2.5 其他生产级功能

| 功能           | Demo      | 生产实现                          | 优先级 |
| -------------- | --------- | --------------------------------- | ------ |
| **流式输出**   | ❌ 无      | ✅ SSE 实时流式传输                | ⭐⭐⭐    |
| **并发控制**   | ❌ 单线程  | ✅ 异步并发 + 限流                 | ⭐⭐⭐⭐   |
| **监控告警**   | ❌ 无      | ✅ Prometheus + Grafana + 钉钉告警 | ⭐⭐⭐⭐⭐  |
| **日志系统**   | `print()` | 结构化日志 + ELK + 链路追踪       | ⭐⭐⭐⭐⭐  |
| **用户管理**   | ❌ 无      | ✅ 多租户 + 权限控制 + 配额管理    | ⭐⭐⭐⭐   |
| **缓存优化**   | ❌ 无      | ✅ Redis 缓存 + 相似查询去重       | ⭐⭐⭐    |
| **数据持久化** | JSON 文件 | PostgreSQL + 对话历史回放         | ⭐⭐⭐⭐   |

---

## 3. 架构升级方案

### 3.1 从单体到微服务

**Demo 架构**（单体应用）:
```
┌─────────────────────────┐
│      Agent Process      │
│  ┌──────────────────┐   │
│  │   LLM Client     │   │
│  ├──────────────────┤   │
│  │   Tool Manager   │   │
│  ├──────────────────┤   │
│  │   Note Tool      │   │
│  └──────────────────┘   │
└─────────────────────────┘
```

**生产架构**（微服务）:
```
┌────────────────────────────────────────────────┐
│                   API Gateway                  │
│          (认证、限流、路由、监控)                │
└────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
┌──────────────┐ ┌─────────────┐ ┌──────────────┐
│ Agent Service│ │ Tool Service│ │ Note Service │
│              │ │             │ │              │
│ - 对话管理    │ │ - 工具执行   │ │ - 向量检索   │
│ - 任务调度    │ │ - 沙箱隔离   │ │ - 笔记管理   │
└──────────────┘ └─────────────┘ └──────────────┘
         │              │              │
         ▼              ▼              ▼
┌────────────────────────────────────────────────┐
│              Infrastructure                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │PostgreSQL│ │  Redis   │ │Milvus/Pinecone│  │
│  └──────────┘ └──────────┘ └──────────────┘   │
└────────────────────────────────────────────────┘
```

### 3.2 可观测性系统

```
┌──────────────────────────────────────────┐
│         Application Layer                │
│  ┌────────────────────────────────────┐  │
│  │  Structured Logging (JSON)         │  │
│  │  - Request ID                      │  │
│  │  - User ID                         │  │
│  │  - Trace ID                        │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────┐
│         Logging & Tracing                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │Filebeat  │ │Logstash  │ │  Jaeger  │ │
│  └──────────┘ └──────────┘ └──────────┘ │
└──────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────┐
│      Storage & Visualization             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │Elasticsearch│ │Prometheus│ │ Grafana │ │
│  └──────────┘ └──────────┘ └──────────┘ │
└──────────────────────────────────────────┘
```

---

## 4. 实施路线图

### Phase 1: 基础增强（1-2月）

**目标**: 提升稳定性和可观测性

- [ ] 结构化日志系统
- [ ] 基础监控（Prometheus + Grafana）
- [ ] 错误告警（钉钉/飞书）
- [ ] 模型 Fallback 机制
- [ ] 基础测试覆盖（80%+）

### Phase 2: 核心功能升级（2-3月）

**目标**: 升级核心组件

- [ ] 向量数据库集成（Milvus）
- [ ] 高级笔记管理系统
- [ ] 上下文截断处理
- [ ] 工具调用验证系统
- [ ] 数据持久化（PostgreSQL）

### Phase 3: 生产优化（2-3月）

**目标**: 生产级性能和安全

- [ ] 流式输出
- [ ] 并发控制和限流
- [ ] 用户认证和权限
- [ ] 缓存优化
- [ ] 链路追踪
- [ ] 灰度发布

### Phase 4: 高级特性（1-2月）

**目标**: 差异化能力

- [ ] Reflection 反思系统
- [ ] 多模型交叉验证
- [ ] 自动纠错机制
- [ ] 对话历史回放
- [ ] A/B 测试框架

---

## 5. 成本估算

### 开发人力

| 阶段     | 人力配置               | 时间      | 成本估算       |
| -------- | ---------------------- | --------- | -------------- |
| Phase 1  | 2 后端 + 1 DevOps      | 1-2月     | ¥30-60万       |
| Phase 2  | 3 后端 + 1 算法        | 2-3月     | ¥60-90万       |
| Phase 3  | 3 后端 + 1 DevOps      | 2-3月     | ¥60-90万       |
| Phase 4  | 2 后端 + 1 算法 + 1 QA | 1-2月     | ¥30-60万       |
| **总计** | **6-8 人团队**         | **6-9月** | **¥180-300万** |

### 基础设施

| 服务        | 配置       | 月成本     | 年成本       |
| ----------- | ---------- | ---------- | ------------ |
| ECS (Agent) | 4C8G × 3   | ¥3000      | ¥36,000      |
| PostgreSQL  | 2C4G (RDS) | ¥1000      | ¥12,000      |
| Redis       | 2C4G       | ¥800       | ¥9,600       |
| Milvus      | 4C8G × 2   | ¥4000      | ¥48,000      |
| 对象存储    | 500GB      | ¥100       | ¥1,200       |
| CDN         | 500GB 流量 | ¥300       | ¥3,600       |
| 监控告警    | 标准版     | ¥500       | ¥6,000       |
| **总计**    | -          | **¥9,700** | **¥116,400** |

### LLM API 成本

| 场景       | QPS | 日调用量 | 日成本（按 M2） | 月成本  |
| ---------- | --- | -------- | --------------- | ------- |
| 小规模测试 | 5   | 100K     | ¥100            | ¥3,000  |
| 中等规模   | 20  | 500K     | ¥500            | ¥15,000 |
| 大规模生产 | 100 | 2M       | ¥2,000          | ¥60,000 |

---

## 6. 总结

### 关键要点

1. **Demo → 生产是 30-40 倍的工作量**
2. **核心难点不在"做"，在"做得稳"**
   - Fallback、验证、监控、容错
3. **投入估算**：6-9 个月 + 6-8 人团队 + ¥200-400万
4. **分阶段实施**：先稳定性，再功能，最后优化

### 下一步

- ✅ 理解 Demo 和生产的差距
- ✅ 评估团队能力和时间预算
- ✅ 确定优先级（参考实施路线图）
- ➡️ 开始 Phase 1 实施

---

**相关文档**:
- [快速开始](../README.md#快速开始)
- [M2 最佳实践](./M2_Agent_Best_Practices_CN.md)
- [开发指南](./DEVELOPMENT.md)

