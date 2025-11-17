# 数据库迁移指南

## 问题描述

如果您遇到以下错误之一：

### 错误 1：历史记录获取失败
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for MessageHistoryResponse
messages.0.id
  Input should be a valid string [type=string_type, input_value=1, input_type=int]
```

### 错误 2：消息保存失败
```
sqlite3.IntegrityError: datatype mismatch
[SQL: INSERT INTO messages (id, session_id, role, content, ...) VALUES (?, ?, ?, ?, ...)]
```

这是因为数据库中存在旧版本的数据，使用的是**整数 ID**，而新版本使用**UUID 字符串 ID**。

## 解决方案

您有两个选择：

### 方案 1：重置数据库（推荐，快速但会丢失数据）

如果您不需要保留现有的会话和消息历史，最简单的方法是重置数据库：

```bash
cd backend
python reset_database.py
```

如果同时需要清理工作空间文件：
```bash
python reset_database.py --clean-workspaces
```

### 方案 2：迁移数据库（保留数据）

如果您想保留现有的数据，可以运行迁移脚本：

```bash
cd backend
python migrate_database.py
```

**注意**：建议先备份数据库文件！
```bash
cp data/database/mini_agent.db data/database/mini_agent.db.backup
```

## 迁移后

重新启动后端服务：
```bash
uvicorn app.main:app --reload
```

## 故障排除

### 如果迁移失败

1. **恢复备份**（如果有）：
   ```bash
   cp data/database/mini_agent.db.backup data/database/mini_agent.db
   ```

2. **检查数据库状态**：
   ```bash
   python diagnose.py
   ```

3. **考虑重置数据库**：
   如果迁移反复失败，可以选择重置数据库重新开始。

### 常见问题

**Q: 为什么会出现这个问题？**
A: 早期版本的代码使用整数作为消息 ID，后来改为使用 UUID 字符串以提供更好的分布式支持和唯一性保证。

**Q: 迁移会影响正在运行的服务吗？**
A: 会。请在迁移前停止后端服务。

**Q: 我可以跳过迁移吗？**
A: 不建议。新代码期望使用 UUID 字符串，旧的整数 ID 会导致错误。

## 技术细节

### 数据库模型变更

**旧版本**：
```python
id = Column(Integer, primary_key=True, autoincrement=True)
```

**新版本**：
```python
id = Column(String(36), primary_key=True)  # UUID 字符串
```

### 修复内容

1. **MessageResponse Schema** - 添加了 field_validator 自动转换 ID 类型
2. **迁移脚本** - migrate_database.py 用于数据迁移
3. **重置脚本** - reset_database.py 用于清理重建

## 预防措施

为了避免将来出现类似问题，现在的代码已经：

1. ✅ 在 Pydantic schema 中添加了类型转换器
2. ✅ 改进了错误消息，提供更清晰的诊断信息
3. ✅ 提供了迁移和重置工具

---

**最后更新**: 2025-11-17
**相关文件**:
- `backend/app/schemas/message.py` - Schema 定义
- `backend/app/models/message.py` - 数据库模型
- `backend/migrate_database.py` - 迁移脚本
- `backend/reset_database.py` - 重置脚本
