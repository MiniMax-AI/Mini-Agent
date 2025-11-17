#!/bin/bash
# 初始化共享环境脚本

set -e  # 遇到错误立即退出

echo "🚀 开始初始化 Mini-Agent 共享环境..."

# 进入后端目录
cd "$(dirname "$0")"
BACKEND_DIR="$(pwd)"

# 创建目录
echo "📁 创建目录结构..."
mkdir -p data/shared_env
mkdir -p data/workspaces
mkdir -p data/database

# 检查 Python 版本
echo "🐍 检查 Python 版本..."
python --version || python3 --version

# 创建虚拟环境
VENV_DIR="data/shared_env/base.venv"
if [ -d "$VENV_DIR" ]; then
    echo "⚠️  虚拟环境已存在，跳过创建"
else
    echo "🔨 创建虚拟环境: $VENV_DIR"
    python -m venv "$VENV_DIR" || python3 -m venv "$VENV_DIR"
fi

# 激活虚拟环境
echo "✨ 激活虚拟环境..."
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
elif [ -f "$VENV_DIR/Scripts/activate" ]; then
    source "$VENV_DIR/Scripts/activate"
else
    echo "❌ 找不到激活脚本"
    exit 1
fi

# 升级 pip
echo "📦 升级 pip..."
pip install --upgrade pip

# 读取允许的包列表并安装
PACKAGES_FILE="data/shared_env/allowed_packages.txt"
if [ -f "$PACKAGES_FILE" ]; then
    echo "📚 安装允许的包..."
    while IFS= read -r package || [ -n "$package" ]; do
        # 跳过空行和注释
        [[ -z "$package" || "$package" =~ ^# ]] && continue
        echo "  📦 安装: $package"
        pip install "$package" || echo "  ⚠️  安装 $package 失败，继续..."
    done < "$PACKAGES_FILE"
else
    echo "⚠️  找不到 allowed_packages.txt，跳过包安装"
fi

echo ""
echo "✅ 共享环境初始化完成！"
echo "📍 虚拟环境路径: $VENV_DIR"
echo ""
