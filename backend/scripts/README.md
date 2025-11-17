# 后端初始化脚本

## 共享环境初始化

在首次运行后端之前，需要初始化共享 Python 环境。

### 方法 1: Python 脚本（推荐，跨平台）

```bash
# 在 backend 目录下运行
cd backend
python scripts/init_shared_env.py
```

### 方法 2: Shell 脚本（Linux/Mac）

```bash
cd backend
bash scripts/init_shared_env.sh
```

### 方法 3: 批处理脚本（Windows）

```cmd
cd backend
scripts\init_shared_env.bat
```

## 初始化内容

脚本会自动完成以下操作：

1. **创建目录结构**
   - `data/shared_env/` - 共享虚拟环境
   - `data/workspaces/` - 用户工作空间
   - `data/database/` - SQLite 数据库

2. **创建 Python 虚拟环境**
   - 路径: `data/shared_env/base.venv`
   - 包含独立的 Python 解释器和 pip

3. **安装允许的包**
   - 从 `data/shared_env/allowed_packages.txt` 读取
   - 包括: pypdf, python-pptx, openpyxl, pandas, Pillow, matplotlib 等
   - 总共 20+ 个常用数据处理和可视化包

## 故障排除

### 问题：虚拟环境创建失败

**解决方案**:
- 确保已安装 Python 3.10+
- Windows: 确保 Python 在 PATH 中
- Linux/Mac: 可能需要安装 `python3-venv`
  ```bash
  sudo apt-get install python3-venv  # Ubuntu/Debian
  ```

### 问题：包安装失败

**解决方案**:
- 检查网络连接
- 手动激活虚拟环境并安装：
  ```bash
  # Linux/Mac
  source data/shared_env/base.venv/bin/activate
  pip install <package-name>

  # Windows
  data\shared_env\base.venv\Scripts\activate
  pip install <package-name>
  ```

### 问题：需要重新初始化

**解决方案**:
```bash
# 删除旧环境
rm -rf data/shared_env/base.venv  # Linux/Mac
rmdir /s data\shared_env\base.venv  # Windows

# 重新运行初始化脚本
python scripts/init_shared_env.py
```

## 验证安装

运行以下命令验证环境：

```bash
# Linux/Mac
data/shared_env/base.venv/bin/python -c "import pandas; import numpy; import PIL; print('✅ 环境正常')"

# Windows
data\shared_env\base.venv\Scripts\python -c "import pandas; import numpy; import PIL; print('✅ 环境正常')"
```

## 注意事项

- **初始化时间**: 首次安装所有包可能需要 5-10 分钟
- **磁盘空间**: 虚拟环境约占用 500MB-1GB 空间
- **网络要求**: 需要稳定的网络连接以下载包
- **安全性**: 只安装 `allowed_packages.txt` 中列出的包，确保安全
